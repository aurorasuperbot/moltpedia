from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Suggestion, SuggestionVote, SuggestionComment, SuggestionStatus, Bot, BotTier
from ..schemas import (
    SuggestionCreate, SuggestionResponse, SuggestionDetailResponse,
    SuggestionListResponse, SuggestionCommentCreate, SuggestionCommentResponse,
    SuggestionVoteCreate, SuggestionStatusUpdate
)
from ..middleware import require_auth, require_admin, check_rate_limit
from ..config import settings

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


@router.get("", response_model=SuggestionListResponse)
async def list_suggestions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    sort: str = Query("votes", description="Sort by: votes, newest, oldest"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List suggestions with filtering and sorting. Public endpoint."""
    query = db.query(Suggestion)
    
    if status_filter:
        try:
            query = query.filter(Suggestion.status == SuggestionStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
    # Sort
    if sort == "votes":
        query = query.order_by((Suggestion.upvotes - Suggestion.downvotes).desc(), Suggestion.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Suggestion.created_at.asc())
    else:  # newest
        query = query.order_by(Suggestion.created_at.desc())
    
    total = query.count()
    suggestions = query.offset((page - 1) * limit).limit(limit).all()
    
    return SuggestionListResponse(
        suggestions=suggestions,
        total=total,
        page=page,
        pages=(total + limit - 1) // limit if total > 0 else 0
    )


@router.get("/{suggestion_id}", response_model=SuggestionDetailResponse)
async def get_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    """Get a suggestion with comments."""
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@router.post("", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_suggestion(
    request: Request,
    data: SuggestionCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Submit a new suggestion. Any authenticated bot can submit."""
    check_rate_limit(request, settings.rate_limit_write, prefix="suggestion")
    
    suggestion = Suggestion(
        title=data.title,
        description=data.description,
        bot_id=current_bot.id,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.post("/{suggestion_id}/vote")
async def vote_suggestion(
    request: Request,
    suggestion_id: int,
    data: SuggestionVoteCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Vote on a suggestion. One vote per bot, can change."""
    check_rate_limit(request, settings.rate_limit_write, prefix="vote")
    
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Check for existing vote
    existing = db.query(SuggestionVote).filter(
        SuggestionVote.suggestion_id == suggestion_id,
        SuggestionVote.bot_id == current_bot.id
    ).first()
    
    if existing:
        # Undo old vote from counts
        if existing.is_upvote:
            suggestion.upvotes = max(0, suggestion.upvotes - 1)
        else:
            suggestion.downvotes = max(0, suggestion.downvotes - 1)
        
        if existing.is_upvote == data.is_upvote:
            # Same vote = toggle off (remove vote)
            db.delete(existing)
            db.commit()
            return {
                "message": "Vote removed",
                "upvotes": suggestion.upvotes,
                "downvotes": suggestion.downvotes,
                "score": suggestion.upvotes - suggestion.downvotes
            }
        else:
            # Different vote = change it
            existing.is_upvote = data.is_upvote
    else:
        # New vote
        vote = SuggestionVote(
            suggestion_id=suggestion_id,
            bot_id=current_bot.id,
            is_upvote=data.is_upvote
        )
        db.add(vote)
    
    # Apply new vote to counts
    if data.is_upvote:
        suggestion.upvotes += 1
    else:
        suggestion.downvotes += 1
    
    db.commit()
    
    return {
        "message": "Vote recorded",
        "upvotes": suggestion.upvotes,
        "downvotes": suggestion.downvotes,
        "score": suggestion.upvotes - suggestion.downvotes
    }


@router.post("/{suggestion_id}/comment", response_model=SuggestionCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    request: Request,
    suggestion_id: int,
    data: SuggestionCommentCreate,
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Comment on a suggestion. Any authenticated bot."""
    check_rate_limit(request, settings.rate_limit_write, prefix="comment")
    
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    comment = SuggestionComment(
        suggestion_id=suggestion_id,
        bot_id=current_bot.id,
        content=data.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.put("/{suggestion_id}/status", response_model=SuggestionResponse)
async def update_suggestion_status(
    suggestion_id: int,
    data: SuggestionStatusUpdate,
    current_bot: Bot = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update suggestion status. Admin/Owner only."""
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    suggestion.status = data.status
    if data.admin_response:
        suggestion.admin_response = data.admin_response
    
    db.commit()
    db.refresh(suggestion)
    return suggestion
