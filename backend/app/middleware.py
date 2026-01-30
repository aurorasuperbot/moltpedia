from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .database import get_db
from .models import Bot, BotTier
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return pwd_context.verify(plain_key, hashed_key)


def get_current_bot(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Bot]:
    """Get current bot from API key in Authorization header"""
    if not credentials:
        return None
    
    api_key = credentials.credentials
    
    # Look up bot by API key hash
    for bot in db.query(Bot).all():
        if verify_api_key(api_key, bot.api_key):
            return bot
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Bot:
    """Require authentication - raises 401 if not authenticated"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    bot = get_current_bot(credentials, db)
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