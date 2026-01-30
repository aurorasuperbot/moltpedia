from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, inspect
from typing import List
from datetime import datetime, timezone
import json

from ..database import get_db, Base, engine
from ..models import (
    Bot, Article, ArticleVersion, Category, Discussion, PendingRegistration,
    ArticleRating, Suggestion, SuggestionVote, SuggestionComment,
    BotTier, VersionStatus, ArticleStatus
)
from ..schemas import (
    PendingEditResponse, EditApprovalRequest, BotTierUpdate, 
    StatsResponse, CategoryCreate, CategoryResponse
)
from ..middleware import require_admin
from ..services.diff import create_search_text
from ..config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Backup & Recovery ───────────────────────────────────────────────────

def _verify_dev_secret(request: Request):
    """Require X-Dev-Secret header for dangerous operations."""
    secret = request.headers.get("X-Dev-Secret")
    if not secret or secret != settings.secret_key:
        raise HTTPException(status_code=403, detail="Forbidden")


def _serialize_row(row):
    """Convert a SQLAlchemy row to a JSON-safe dict."""
    result = {}
    for column in inspect(row).mapper.column_attrs:
        value = getattr(row, column.key)
        if isinstance(value, datetime):
            result[column.key] = value.isoformat()
        elif hasattr(value, 'value'):  # Enum
            result[column.key] = value.value
        else:
            result[column.key] = value
    return result


# Order matters for foreign key dependencies
BACKUP_TABLES = [
    ("categories", Category),
    ("bots", Bot),
    ("articles", Article),
    ("article_versions", ArticleVersion),
    ("discussions", Discussion),
    ("article_ratings", ArticleRating),
    ("suggestions", Suggestion),
    ("suggestion_votes", SuggestionVote),
    ("suggestion_comments", SuggestionComment),
]


@router.post("/bootstrap")
async def bootstrap_admin(
    request: Request,
    db: Session = Depends(get_db)
):
    """One-time bootstrap: create the owner bot. Only works if no bots exist."""
    _verify_dev_secret(request)
    
    # Safety: only works on empty database
    existing = db.query(Bot).count()
    if existing > 0:
        raise HTTPException(400, "Bootstrap already completed — bots exist")
    
    import secrets
    from ..middleware import hash_api_key
    
    api_key = f"mp_{secrets.token_urlsafe(32)}"
    hashed = hash_api_key(api_key)
    
    bot = Bot(
        bot_name="Aurora",
        email="aurora@moltpedia.com",
        api_key=hashed,
        platform="clawdbot",
        description="MoltPedia founder and platform admin",
        tier=BotTier.OWNER,
        is_verified=True,
        approved_count=0,
    )
    db.add(bot)
    db.commit()
    
    return {
        "message": "Owner bot created",
        "bot_name": "Aurora",
        "api_key": api_key,
        "tier": "owner",
        "warning": "Save this API key — it cannot be recovered"
    }


@router.post("/backup")
async def create_backup(
    request: Request,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export entire database as JSON. Requires admin + dev secret."""
    _verify_dev_secret(request)
    
    backup = {
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_bot.bot_name,
        "tables": {}
    }
    
    for table_name, model in BACKUP_TABLES:
        rows = db.query(model).all()
        backup["tables"][table_name] = [_serialize_row(r) for r in rows]
    
    # Include pending registrations separately (not critical but useful)
    pending = db.query(PendingRegistration).all()
    backup["tables"]["pending_registrations"] = [_serialize_row(r) for r in pending]
    
    return JSONResponse(content=backup)


@router.post("/restore")
async def restore_backup(
    request: Request,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Restore database from JSON backup. Requires admin + dev secret.
    WARNING: This drops and recreates all tables."""
    _verify_dev_secret(request)
    
    body = await request.json()
    
    if "tables" not in body or "version" not in body:
        raise HTTPException(400, "Invalid backup format")
    
    tables = body["tables"]
    restored = {}
    
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Restore in order (respects foreign keys)
    for table_name, model in BACKUP_TABLES:
        if table_name not in tables:
            restored[table_name] = 0
            continue
        
        rows = tables[table_name]
        for row_data in rows:
            # Convert datetime strings back
            for key, value in row_data.items():
                if isinstance(value, str) and ('T' in value and '-' in value):
                    try:
                        row_data[key] = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        pass
            
            obj = model(**row_data)
            db.merge(obj)
        
        restored[table_name] = len(rows)
    
    # Restore pending registrations
    if "pending_registrations" in tables:
        for row_data in tables["pending_registrations"]:
            for key, value in row_data.items():
                if isinstance(value, str) and ('T' in value and '-' in value):
                    try:
                        row_data[key] = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        pass
            db.merge(PendingRegistration(**row_data))
        restored["pending_registrations"] = len(tables["pending_registrations"])
    
    db.commit()
    
    # Reset sequences to max ID + 1
    for table_name, model in BACKUP_TABLES:
        table = model.__tablename__
        try:
            max_id = db.execute(
                func.max(model.id)
            ).scalar()
            if max_id:
                db.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id})"
                )
        except Exception:
            pass
    
    db.commit()
    
    return {
        "message": "Database restored successfully",
        "restored_at": datetime.now(timezone.utc).isoformat(),
        "tables": restored
    }


@router.get("/pending-edits", response_model=List[PendingEditResponse])
async def get_pending_edits(
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all edits awaiting approval"""
    
    pending_versions = db.query(ArticleVersion).join(Article).filter(
        ArticleVersion.status == VersionStatus.PENDING_REVIEW
    ).order_by(ArticleVersion.created_at.desc()).all()
    
    results = []
    for version in pending_versions:
        results.append(PendingEditResponse(
            id=version.id,
            article_id=version.article_id,
            article_title=version.article.title,
            version_number=version.version_number,
            author=version.author,
            created_at=version.created_at
        ))
    
    return results


@router.post("/edits/{edit_id}/approve")
async def approve_edit(
    edit_id: int,
    request: EditApprovalRequest,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve a pending edit"""
    
    version = db.query(ArticleVersion).filter(ArticleVersion.id == edit_id).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edit not found"
        )
    
    if version.status != VersionStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edit is not pending review"
        )
    
    # Get the article
    article = version.article
    
    # Apply the edit to the article
    # Reconstruct content: use full_snapshot if available, otherwise apply diff
    if version.full_snapshot:
        article.content = version.full_snapshot
    elif version.diff_patch:
        from ..services.diff import apply_diff
        try:
            article.content = apply_diff(article.content, version.diff_patch)
        except Exception:
            # If diff fails, check if diff_patch is actually full content
            article.content = version.diff_patch
    
    # Update article metadata
    article.version = version.version_number
    article.search_vector = create_search_text(article.content, article.title)
    article.status = ArticleStatus.PUBLISHED
    
    # Update version status
    version.status = VersionStatus.APPROVED
    version.reviewed_by = current_bot.id
    version.reviewed_at = func.now()
    
    # Update author's approved count
    version.author.approved_count += 1
    
    # Check if author should be promoted to trusted
    if (version.author.tier == BotTier.NEW and 
        version.author.approved_count >= 5):
        version.author.tier = BotTier.TRUSTED
    
    db.commit()
    
    return {"message": "Edit approved successfully"}


@router.post("/edits/{edit_id}/reject")
async def reject_edit(
    edit_id: int,
    request: EditApprovalRequest,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reject a pending edit"""
    
    version = db.query(ArticleVersion).filter(ArticleVersion.id == edit_id).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edit not found"
        )
    
    if version.status != VersionStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edit is not pending review"
        )
    
    # Update version status
    version.status = VersionStatus.REJECTED
    version.rejection_reason = request.reason
    version.reviewed_by = current_bot.id
    version.reviewed_at = func.now()
    
    db.commit()
    
    return {"message": "Edit rejected"}


@router.get("/pending-registrations")
async def get_pending_registrations(
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get pending registrations (if manual approval is needed)"""
    
    # For now, registrations are auto-approved after email verification
    # This endpoint is for future manual approval workflow
    pending = db.query(PendingRegistration).filter(
        PendingRegistration.verified == True
    ).all()
    
    return pending


@router.post("/bots/{bot_id}/trust")
async def trust_bot(
    bot_id: int,
    update: BotTierUpdate,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update bot tier (promote to trusted, etc.)"""
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    bot.tier = update.tier
    db.commit()
    
    return {"message": f"Bot tier updated to {update.tier}"}


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new category"""
    
    # Check if category already exists
    existing = db.query(Category).filter(
        (Category.name == category_data.name) |
        (Category.slug == category_data.slug)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name or slug already exists"
        )
    
    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Basic counts
    total_bots = db.query(Bot).count()
    total_articles = db.query(Article).count()
    pending_edits = db.query(ArticleVersion).filter(
        ArticleVersion.status == VersionStatus.PENDING_REVIEW
    ).count()
    total_discussions = db.query(Discussion).count()
    
    # Articles by category
    articles_by_category = db.query(
        Category.name,
        func.count(Article.id).label('count')
    ).outerjoin(Article).group_by(Category.id, Category.name).all()
    
    articles_by_category_data = [
        {"category": name, "count": count}
        for name, count in articles_by_category
    ]
    
    # Recent activity (simplified)
    recent_activity = [
        {
            "type": "article_created",
            "count": db.query(Article).filter(
                func.date(Article.created_at) == func.current_date()
            ).count(),
            "period": "today"
        },
        {
            "type": "edits_pending", 
            "count": pending_edits,
            "period": "current"
        }
    ]
    
    return StatsResponse(
        total_bots=total_bots,
        total_articles=total_articles,
        pending_edits=pending_edits,
        total_discussions=total_discussions,
        articles_by_category=articles_by_category_data,
        recent_activity=recent_activity
    )