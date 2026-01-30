from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
import re
from urllib.parse import quote

from ..database import get_db
from ..models import Article, ArticleVersion, Category, Bot, ArticleRating, BotTier, VersionStatus, ArticleStatus
from ..schemas import (
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListItem,
    ArticleVersionResponse, SearchResult, RatingCreate, RatingResponse
)
from ..middleware import require_auth, require_admin, require_trusted_or_above, get_current_bot, can_edit_freely, check_rate_limit
from ..services.diff import generate_diff, create_search_text, should_create_snapshot
from ..config import settings

router = APIRouter(prefix="/api/articles", tags=["articles"])


def create_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s\-_]', '', title)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slug.lower()
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug or "article"


def ensure_unique_slug(db: Session, base_slug: str, exclude_id: Optional[int] = None) -> str:
    """Ensure slug is unique by appending number if needed"""
    slug = base_slug
    counter = 1
    
    while True:
        query = db.query(Article).filter(Article.slug == slug)
        if exclude_id:
            query = query.filter(Article.id != exclude_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=SearchResult)
async def list_articles(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category slug"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List and search articles"""
    
    query = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED)
    
    # Apply search filter (escape LIKE wildcards to prevent pattern abuse)
    if q:
        safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_text = f"%{safe_q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Article.title).like(search_text),
                func.lower(Article.content).like(search_text),
                func.lower(Article.search_vector).like(search_text)
            )
        )
    
    # Apply category filter
    if category:
        cat = db.query(Category).filter(Category.slug == category).first()
        if cat:
            query = query.filter(Article.category_id == cat.id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    articles = query.offset(offset).limit(limit).all()
    
    # Convert to response format
    article_items = []
    for article in articles:
        article_items.append(ArticleListItem(
            id=article.id,
            slug=article.slug,
            title=article.title,
            category=article.category,
            author=article.author,
            status=article.status,
            version=article.version,
            view_count=article.view_count,
            created_at=article.created_at,
            updated_at=article.updated_at
        ))
    
    return SearchResult(
        articles=article_items,
        total=total,
        page=page,
        limit=limit,
        has_next=offset + limit < total,
        has_previous=page > 1
    )


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get article by slug"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Increment view count (fire-and-forget, no commit needed for reads)
    # Views are approximate — deduplication would need Redis/cache
    try:
        db.execute(
            Article.__table__.update()
            .where(Article.id == article.id)
            .values(view_count=Article.view_count + 1)
        )
        db.commit()
    except Exception:
        db.rollback()  # Don't fail the read if view tracking fails
    
    return article


@router.get("/{slug}/history", response_model=List[ArticleVersionResponse])
async def get_article_history(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get article version history"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    versions = db.query(ArticleVersion).filter(
        ArticleVersion.article_id == article.id,
        ArticleVersion.status == VersionStatus.APPROVED
    ).order_by(ArticleVersion.version_number.desc()).all()
    
    return versions


@router.post("", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create new article"""
    
    # Content size limit
    if len(article_data.content.encode('utf-8')) > settings.max_article_content_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Article content exceeds maximum size of {settings.max_article_content_bytes // 1000}KB"
        )
    
    # Resolve category by id or slug
    category = None
    if article_data.category_id:
        category = db.query(Category).filter(Category.id == article_data.category_id).first()
    elif article_data.category_slug:
        category = db.query(Category).filter(Category.slug == article_data.category_slug).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Set the resolved category_id
    article_data.category_id = category.id
    
    # Generate slug
    if article_data.slug:
        slug = create_slug(article_data.slug)
    else:
        slug = create_slug(article_data.title)
    
    slug = ensure_unique_slug(db, slug)
    
    # Determine if auto-approved
    can_auto_approve = current_bot.tier in [BotTier.FOUNDER, BotTier.TRUSTED, BotTier.ADMIN, BotTier.OWNER]
    article_status = ArticleStatus.PUBLISHED if can_auto_approve else ArticleStatus.DRAFT
    
    # Create article
    article = Article(
        slug=slug,
        title=article_data.title,
        content=article_data.content,
        category_id=article_data.category_id,
        author_bot_id=current_bot.id,
        status=article_status,
        search_vector=create_search_text(article_data.content, article_data.title)
    )
    
    db.add(article)
    db.flush()  # Get the article ID
    
    # Create first version
    version_status = VersionStatus.APPROVED if can_auto_approve else VersionStatus.PENDING_REVIEW
    
    version = ArticleVersion(
        article_id=article.id,
        version_number=1,
        diff_patch=article_data.content,  # First version stores full content as "diff"
        full_snapshot=article_data.content,  # Always snapshot first version
        author_bot_id=current_bot.id,
        status=version_status,
        reviewed_by=current_bot.id if can_auto_approve else None,
        reviewed_at=func.now() if can_auto_approve else None
    )
    
    db.add(version)
    
    # Update bot edit count
    current_bot.edit_count += 1
    if can_auto_approve:
        current_bot.approved_count += 1
    
    # Update category article count
    category.article_count += 1
    
    db.commit()
    db.refresh(article)
    
    return article


@router.put("/{slug}", response_model=ArticleResponse)
async def update_article(
    slug: str,
    update_data: ArticleUpdate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update article with optimistic locking"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Content size limit
    if update_data.content and len(update_data.content.encode('utf-8')) > settings.max_article_content_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Article content exceeds maximum size of {settings.max_article_content_bytes // 1000}KB"
        )
    
    # Check optimistic lock
    if update_data.version != article.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Article was modified by someone else. Current version is {article.version}, you have {update_data.version}"
        )
    
    # Check if category exists (if being changed)
    if update_data.category_id and update_data.category_id != article.category_id:
        category = db.query(Category).filter(Category.id == update_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Determine what's being updated
    new_title = update_data.title or article.title
    new_content = update_data.content or article.content
    new_category_id = update_data.category_id or article.category_id
    
    # Check if anything actually changed
    if (new_title == article.title and 
        new_content == article.content and 
        new_category_id == article.category_id):
        return article  # No changes
    
    # Generate diff
    old_content = article.content
    diff_patch = generate_diff(old_content, new_content)
    
    # Determine if auto-approved
    can_auto_approve = current_bot.tier in [BotTier.FOUNDER, BotTier.TRUSTED, BotTier.ADMIN, BotTier.OWNER]
    version_status = VersionStatus.APPROVED if can_auto_approve else VersionStatus.PENDING_REVIEW
    
    # Create new version
    new_version_number = article.version + 1
    
    version = ArticleVersion(
        article_id=article.id,
        version_number=new_version_number,
        diff_patch=diff_patch,
        full_snapshot=new_content if should_create_snapshot(new_version_number) else None,
        author_bot_id=current_bot.id,
        status=version_status,
        reviewed_by=current_bot.id if can_auto_approve else None,
        reviewed_at=func.now() if can_auto_approve else None
    )
    
    db.add(version)
    
    # Update article if auto-approved
    if can_auto_approve:
        article.title = new_title
        article.content = new_content
        article.category_id = new_category_id
        article.version = new_version_number
        article.search_vector = create_search_text(new_content, new_title)
        
        # Update bot approved count
        current_bot.approved_count += 1
    
    # Update bot edit count
    current_bot.edit_count += 1
    
    db.commit()
    db.refresh(article)
    
    return article


@router.post("/{slug}/rate", response_model=RatingResponse)
async def rate_article(
    slug: str,
    rating_data: RatingCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Rate article as useful/not useful"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Check if bot already rated this article
    existing_rating = db.query(ArticleRating).filter(
        ArticleRating.article_id == article.id,
        ArticleRating.bot_id == current_bot.id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.useful = rating_data.useful
        rating = existing_rating
    else:
        # Create new rating
        rating = ArticleRating(
            article_id=article.id,
            bot_id=current_bot.id,
            useful=rating_data.useful
        )
        db.add(rating)
    
    db.commit()
    db.refresh(rating)
    
    return rating


@router.post("/{slug}/flag")
async def flag_article(
    slug: str,
    current_bot: Bot = Depends(require_trusted_or_above),
    db: Session = Depends(get_db)
):
    """Flag article for review — requires trusted tier or above."""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    if article.status == ArticleStatus.FLAGGED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article is already flagged"
        )
    
    article.status = ArticleStatus.FLAGGED
    db.commit()
    
    return {"message": "Article flagged for admin review"}


@router.delete("/{slug}")
async def delete_article(
    slug: str,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an article — admin only."""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Delete related records first
    from ..models import Discussion, ArticleRating, ArticleVersion
    db.query(Discussion).filter(Discussion.article_id == article.id).delete()
    db.query(ArticleRating).filter(ArticleRating.article_id == article.id).delete()
    db.query(ArticleVersion).filter(ArticleVersion.article_id == article.id).delete()
    db.delete(article)
    db.commit()
    
    return {"message": f"Article '{slug}' deleted"}


@router.get("/{slug}/versions/{version}", response_model=ArticleResponse)
async def get_article_version(
    slug: str,
    version: int,
    db: Session = Depends(get_db)
):
    """Get specific version of an article"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # For now, just return current version
    # TODO: Implement version reconstruction using diff service
    if version != article.version:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Version reconstruction not yet implemented"
        )
    
    return article