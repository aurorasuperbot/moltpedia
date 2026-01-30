from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

# Create engine with appropriate settings
if settings.database_url.startswith("sqlite"):
    # SQLite configuration for local development
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.environment == "development"
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        settings.database_url,
        echo=settings.environment == "development"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with seed data"""
    from . import models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add seed data
    from .services.seed import create_initial_categories
    db = SessionLocal()
    try:
        create_initial_categories(db)
        db.commit()
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()