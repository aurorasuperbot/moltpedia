from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import (
    Bot, Article, ArticleVersion, Category, Discussion, PendingRegistration,
    BotTier, VersionStatus, ArticleStatus
)
from ..schemas import (
    PendingEditResponse, EditApprovalRequest, BotTierUpdate, 
    StatsResponse, CategoryCreate, CategoryResponse
)
from ..middleware import require_admin
from ..services.diff import create_search_text

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
    # Note: For simplicity, assuming we can reconstruct from the version
    # In a full implementation, you'd use the diff service to reconstruct content
    if version.full_snapshot:
        article.content = version.full_snapshot
    else:
        # For now, use the diff_patch as content
        # This is simplified - proper implementation would reconstruct from diffs
        pass
    
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