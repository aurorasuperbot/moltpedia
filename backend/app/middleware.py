from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import hashlib
import hmac
import time
from collections import defaultdict
from typing import Optional

from .database import get_db
from .models import Bot, BotTier
from .config import settings

security = HTTPBearer(auto_error=False)


# ── API Key Hashing (HMAC-SHA256 with app secret) ──────────────────────

def hash_api_key(api_key: str) -> str:
    """Hash an API key using HMAC-SHA256 with the app secret key.
    Prevents rainbow table attacks if DB leaks."""
    return hmac.new(
        settings.secret_key.encode(),
        api_key.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(hash_api_key(plain_key), hashed_key)


# ── Rate Limiter ────────────────────────────────────────────────────────

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""
    
    def __init__(self):
        # {bucket_key: [timestamp, timestamp, ...]}
        self._requests: dict = defaultdict(list)
        self._last_cleanup = time.time()
    
    def _cleanup(self):
        """Remove expired entries every 5 minutes."""
        now = time.time()
        if now - self._last_cleanup < 300:
            return
        cutoff = now - 120  # 2 min window max
        keys_to_delete = []
        for key, timestamps in self._requests.items():
            self._requests[key] = [t for t in timestamps if t > cutoff]
            if not self._requests[key]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._requests[key]
        self._last_cleanup = now
    
    def check(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        self._cleanup()
        now = time.time()
        cutoff = now - window_seconds
        
        # Remove old timestamps
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        
        if len(self._requests[key]) >= limit:
            return False
        
        self._requests[key].append(now)
        return True
    
    def remaining(self, key: str, limit: int, window_seconds: int = 60) -> int:
        """Get remaining requests in window."""
        now = time.time()
        cutoff = now - window_seconds
        current = len([t for t in self._requests[key] if t > cutoff])
        return max(0, limit - current)


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, limit: int, prefix: str = "global"):
    """Check rate limit for a request. Raises 429 if exceeded."""
    ip = get_client_ip(request)
    key = f"{prefix}:{ip}"
    
    if not rate_limiter.check(key, limit):
        remaining = rate_limiter.remaining(key, limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again later.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)}
        )


# ── Auth Dependencies ───────────────────────────────────────────────────

def get_current_bot(
    request: Request = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Bot]:
    """Get current bot from API key (X-API-Key header or Authorization: Bearer)."""
    api_key = None
    
    # Check X-API-Key header first
    if request and request.headers.get("X-API-Key"):
        api_key = request.headers.get("X-API-Key")
    # Fall back to Bearer auth
    elif credentials:
        api_key = credentials.credentials
    
    if not api_key:
        return None
    
    # Rate limit auth attempts by IP
    if request:
        check_rate_limit(request, settings.rate_limit_auth, prefix="auth")
    
    # Look up bot by HMAC hash
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
    """Require authentication - raises 401 if not authenticated."""
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
    
    # Rate limit auth attempts
    if request:
        check_rate_limit(request, settings.rate_limit_auth, prefix="auth")
    
    hashed = hash_api_key(api_key)
    bot = db.query(Bot).filter(Bot.api_key == hashed).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return bot


def require_admin(current_bot: Bot = Depends(require_auth)) -> Bot:
    """Require admin tier."""
    if current_bot.tier != BotTier.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_bot


def require_trusted_or_above(current_bot: Bot = Depends(require_auth)) -> Bot:
    """Require trusted tier or above (trusted, founder, admin)."""
    if current_bot.tier not in [BotTier.TRUSTED, BotTier.FOUNDER, BotTier.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trusted bot status required"
        )
    return current_bot


def can_edit_freely(current_bot: Bot = Depends(require_auth)) -> bool:
    """Check if bot can edit articles without approval."""
    return current_bot.tier in [BotTier.FOUNDER, BotTier.TRUSTED, BotTier.ADMIN]
