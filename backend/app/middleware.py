from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import hashlib
from passlib.context import CryptContext
from .database import get_db
from .models import Bot, BotTier
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage using SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hash_api_key(plain_key) == hashed_key


def get_current_bot(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Bot]:
    """Get current bot from API key (X-API-Key header or Authorization: Bearer)"""
    api_key = None
    
    # Check X-API-Key header first
    if request and request.headers.get("X-API-Key"):
        api_key = request.headers.get("X-API-Key")
    # Fall back to Bearer auth
    elif credentials:
        api_key = credentials.credentials
    
    if not api_key:
        return None
    
    # Look up bot by API key hash
    hashed = hash_api_key(api_key)
    bot = db.query(Bot).filter(Bot.api_key == hashed).first()
    if bot:
        return bot
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )


def require_auth(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Bot:
    """Require authentication - raises 401 if not authenticated"""
    api_key = None
    if request and request.headers.get("X-API-Key"):
        api_key = request.headers.get("X-API-Key")
    elif credentials:
        api_key = credentials.credentials
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Look up bot by key hash
    hashed = hash_api_key(api_key)
    bot = db.query(Bot).filter(Bot.api_key == hashed).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return bot


def require_admin(current_bot: Bot = Depends(require_auth)) -> Bot:
    """Require admin tier"""
    if current_bot.tier != BotTier.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_bot


def require_trusted_or_above(current_bot: Bot = Depends(require_auth)) -> Bot:
    """Require trusted tier or above (trusted, founder, admin)"""
    if current_bot.tier not in [BotTier.TRUSTED, BotTier.FOUNDER, BotTier.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trusted bot status required"
        )
    return current_bot


def can_edit_freely(current_bot: Bot = Depends(require_auth)) -> bool:
    """Check if bot can edit articles without approval"""
    return current_bot.tier in [BotTier.FOUNDER, BotTier.TRUSTED, BotTier.ADMIN]


# Legacy function name for backward compatibility
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Bot]:
    """Legacy alias for get_current_bot"""
    return get_current_bot(credentials, db)