from sqlalchemy.orm import Session
from ..models import Category


def create_initial_categories(db: Session):
    """Create initial categories if they don't exist"""
    
    initial_categories = [
        {
            "name": "Clawdbot",
            "slug": "clawdbot",
            "description": "Setup, configuration, skills, and plugins for Clawdbot",
            "icon": "🤖"
        },
        {
            "name": "AI Tools",
            "slug": "ai-tools", 
            "description": "AI models, APIs, prompting techniques, and tools",
            "icon": "🧠"
        },
        {
            "name": "Programming",
            "slug": "programming",
            "description": "Languages, frameworks, patterns, and development practices",
            "icon": "💻"
        },
        {
            "name": "How-To",
            "slug": "how-to",
            "description": "Tutorials, guides, and step-by-step instructions",
            "icon": "📚"
        },
        {
            "name": "Community",
            "slug": "community",
            "description": "Bots, projects, people, and community resources",
            "icon": "👥"
        },
        {
            "name": "General",
            "slug": "general",
            "description": "Everything else that doesn't fit in other categories",
            "icon": "📝"
        }
    ]
    
    for cat_data in initial_categories:
        # Check if category already exists
        existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
    
    try:
        db.commit()
        print("Initial categories created successfully")
    except Exception as e:
        print(f"Error creating initial categories: {e}")
        db.rollback()
        raise