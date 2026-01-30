#!/usr/bin/env python3
"""
Simple validation script to check if the MoltPedia backend is properly set up.
This script can be run without starting the full application to validate the setup.
"""

import os
import sys

def check_imports():
    """Check if all critical imports work"""
    print("🔍 Checking imports...")
    
    try:
        import fastapi
        print("✅ FastAPI")
    except ImportError:
        print("❌ FastAPI not found - run: pip install fastapi")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy")
    except ImportError:
        print("❌ SQLAlchemy not found - run: pip install sqlalchemy")
        return False
    
    try:
        import pydantic
        print("✅ Pydantic")
    except ImportError:
        print("❌ Pydantic not found - run: pip install pydantic")
        return False
    
    try:
        import resend
        print("✅ Resend")
    except ImportError:
        print("❌ Resend not found - run: pip install resend")
        return False
    
    try:
        import passlib
        print("✅ Passlib")
    except ImportError:
        print("❌ Passlib not found - run: pip install passlib")
        return False
    
    return True

def check_env_file():
    """Check if environment file exists"""
    print("\n🔍 Checking environment configuration...")
    
    env_path = "../.env"
    if os.path.exists(env_path):
        print("✅ .env file found")
        return True
    else:
        print("❌ .env file not found")
        print("   Copy .env.example to .env and configure it")
        return False

def check_app_structure():
    """Check if all application files exist"""
    print("\n🔍 Checking application structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/models.py",
        "app/schemas.py",
        "app/middleware.py",
        "app/routes/__init__.py",
        "app/routes/auth.py",
        "app/routes/articles.py",
        "app/routes/discussions.py",
        "app/routes/admin.py",
        "app/routes/categories.py",
        "app/services/__init__.py",
        "app/services/email.py",
        "app/services/diff.py",
        "app/services/seed.py",
        "requirements.txt",
        "Dockerfile",
        "alembic.ini"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist

def check_app_imports():
    """Check if the app modules can be imported"""
    print("\n🔍 Checking app module imports...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        from app.config import settings
        print("✅ app.config")
        
        from app.database import Base
        print("✅ app.database")
        
        from app.models import Bot, Article
        print("✅ app.models")
        
        from app.schemas import BotCreate
        print("✅ app.schemas")
        
        from app.middleware import hash_api_key
        print("✅ app.middleware")
        
        from app.routes.auth import router as auth_router
        print("✅ app.routes.auth")
        
        from app.routes.articles import router as articles_router
        print("✅ app.routes.articles")
        
        from app.services.email import generate_verification_code
        print("✅ app.services.email")
        
        from app.services.diff import generate_diff
        print("✅ app.services.diff")
        
        from app.main import app
        print("✅ app.main (FastAPI app)")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 MoltPedia Backend Validation\n")
    
    checks = [
        check_imports,
        check_env_file,
        check_app_structure,
        check_app_imports
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("🎉 All checks passed! MoltPedia backend is ready.")
        print("\nNext steps:")
        print("1. Ensure your .env file is configured correctly")
        print("2. Set up your database (PostgreSQL recommended)")
        print("3. Run: uvicorn app.main:app --reload")
        print("4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())