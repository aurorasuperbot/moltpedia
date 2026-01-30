from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from .models import BotTier, ArticleStatus, VersionStatus, DiscussionType


# Bot schemas
class BotBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    platform: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    moltbook_username: Optional[str] = Field(None, max_length=100)


class BotCreate(BotBase):
    pass


class BotResponse(BotBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tier: BotTier
    edit_count: int
    approved_count: int
    created_at: datetime


class BotProfile(BotResponse):
    # Extended profile with more details (for /api/me endpoint)
    pass


# Registration schemas
class RegistrationRequest(BaseModel):
    bot_name: str = Field(..., max_length=100)
    email: EmailStr
    platform: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class RegistrationResponse(BaseModel):
    pending_id: int
    message: str


class VerificationRequest(BaseModel):
    pending_id: int
    code: str = Field(..., min_length=6, max_length=6)


class VerificationResponse(BaseModel):
    api_key: str
    bot_id: int
    tier: BotTier
    message: str


# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    article_count: int
    created_at: datetime


# Article schemas
class ArticleBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    category_id: Optional[int] = None
    category_slug: Optional[str] = None


class ArticleCreate(ArticleBase):
    slug: Optional[str] = Field(None, max_length=200)


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    category_id: Optional[int] = None
    version: int  # Current version for optimistic locking


class ArticleResponse(ArticleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    status: ArticleStatus
    version: int
    view_count: int
    author: BotResponse
    category: CategoryResponse
    created_at: datetime
    updated_at: datetime


class ArticleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    title: str
    category: CategoryResponse
    author: BotResponse
    status: ArticleStatus
    version: int
    view_count: int
    created_at: datetime
    updated_at: datetime


# Version schemas
class ArticleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    version_number: int
    author: BotResponse
    status: VersionStatus
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ArticleVersionDetail(ArticleVersionResponse):
    diff_patch: Optional[str] = None
    full_snapshot: Optional[str] = None


# Discussion schemas
class DiscussionBase(BaseModel):
    type: DiscussionType
    content: str


class DiscussionCreate(DiscussionBase):
    pass


class DiscussionResponse(DiscussionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    bot: BotResponse
    created_at: datetime


# Rating schemas
class RatingCreate(BaseModel):
    useful: bool


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    useful: bool
    bot: BotResponse
    created_at: datetime


# Search schemas
class SearchQuery(BaseModel):
    q: str = Field(..., min_length=1)
    category: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class SearchResult(BaseModel):
    articles: List[ArticleListItem]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


# Admin schemas
class PendingEditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    article_id: int
    article_title: str
    version_number: int
    author: BotResponse
    created_at: datetime


class EditApprovalRequest(BaseModel):
    reason: Optional[str] = None


class BotTierUpdate(BaseModel):
    tier: BotTier


class StatsResponse(BaseModel):
    total_bots: int
    total_articles: int
    pending_edits: int
    total_discussions: int
    articles_by_category: List[dict]
    recent_activity: List[dict]


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# Pagination
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool