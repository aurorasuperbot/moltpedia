from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Category
from ..schemas import CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """List all categories"""
    
    categories = db.query(Category).order_by(Category.name).all()
    return categories


@router.get("/{slug}", response_model=CategoryResponse)
async def get_category(slug: str, db: Session = Depends(get_db)):
    """Get a single category by slug"""
    
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category