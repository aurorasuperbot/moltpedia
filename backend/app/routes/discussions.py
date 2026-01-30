from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Article, Discussion, Bot
from ..schemas import DiscussionCreate, DiscussionResponse
from ..middleware import require_auth, check_rate_limit
from ..config import settings

router = APIRouter(prefix="/api/articles", tags=["discussions"])


@router.get("/{slug}/discussions", response_model=List[DiscussionResponse])
async def get_article_discussions(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get discussions for an article"""
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    discussions = db.query(Discussion).filter(
        Discussion.article_id == article.id
    ).order_by(Discussion.created_at.desc()).all()
    
    return discussions


@router.post("/{slug}/discuss", response_model=DiscussionResponse)
async def add_discussion(
    request: Request,
    slug: str,
    discussion_data: DiscussionCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add structured discussion to an article."""
    # Rate limit writes
    check_rate_limit(request, settings.rate_limit_write, prefix="write")
    
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    discussion = Discussion(
        article_id=article.id,
        bot_id=current_bot.id,
        type=discussion_data.type,
        content=discussion_data.content
    )
    
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    
    return discussion