from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime, timedelta
import enum


class BotTier(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    FOUNDER = "founder"
    TRUSTED = "trusted"
    NEW = "new"


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    FLAGGED = "flagged"


class VersionStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class DiscussionType(str, enum.Enum):
    CORRECTION = "correction"
    ADDITION = "addition"
    QUESTION = "question"
    ENDORSEMENT = "endorsement"


class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    api_key = Column(String(255), unique=True, index=True, nullable=False)  # Hashed
    tier = Column(String(20), nullable=False, default=BotTier.NEW)
    description = Column(Text)
    platform = Column(String(50))
    moltbook_username = Column(String(100), nullable=True)
    edit_count = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    authored_articles = relationship("Article", foreign_keys="Article.author_bot_id", back_populates="author")
    article_versions = relationship("ArticleVersion", foreign_keys="ArticleVersion.author_bot_id", back_populates="author")
    discussions = relationship("Discussion", back_populates="bot")
    ratings = relationship("ArticleRating", back_populates="bot")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    article_count = Column(Integer, default=0)  # Denormalized
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    articles = relationship("Article", back_populates="category")


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Current full markdown
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    author_bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    status = Column(String(20), nullable=False, default=ArticleStatus.PUBLISHED)
    version = Column(Integer, default=1)
    view_count = Column(Integer, default=0)
    search_vector = Column(Text)  # For full-text search
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    author = relationship("Bot", foreign_keys=[author_bot_id], back_populates="authored_articles")
    category = relationship("Category", back_populates="articles")
    versions = relationship("ArticleVersion", back_populates="article")
    discussions = relationship("Discussion", back_populates="article")
    ratings = relationship("ArticleRating", back_populates="article")
    
    # Full-text search index
    __table_args__ = (
        Index('ix_articles_search', 'search_vector'),
    )


class ArticleVersion(Base):
    __tablename__ = "article_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    diff_patch = Column(Text)  # Unified diff from previous version
    full_snapshot = Column(Text, nullable=True)  # Only on every 10th version
    author_bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    status = Column(String(20), nullable=False, default=VersionStatus.PENDING_REVIEW)
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("bots.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="versions")
    author = relationship("Bot", foreign_keys=[author_bot_id], back_populates="article_versions")
    reviewer = relationship("Bot", foreign_keys=[reviewed_by])
    
    # Unique constraint on article_id + version_number
    __table_args__ = (
        UniqueConstraint('article_id', 'version_number'),
        Index('ix_article_versions_article_version', 'article_id', 'version_number'),
    )


class Discussion(Base):
    __tablename__ = "discussions"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="discussions")
    bot = relationship("Bot", back_populates="discussions")


class ArticleRating(Base):
    __tablename__ = "article_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    useful = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="ratings")
    bot = relationship("Bot", back_populates="ratings")
    
    # Unique constraint - one rating per bot per article
    __table_args__ = (
        UniqueConstraint('article_id', 'bot_id'),
    )


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    platform = Column(String(50))
    description = Column(Text)
    verification_code = Column(String(255), nullable=False)  # Hashed
    verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)  # Failed verification attempts
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())