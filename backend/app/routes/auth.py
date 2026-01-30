from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string

from ..database import get_db
from ..models import Bot, PendingRegistration, BotTier
from ..schemas import (
    RegistrationRequest, RegistrationResponse,
    VerificationRequest, VerificationResponse,
    BotProfile
)
from ..services.email import (
    generate_verification_code, hash_verification_code, 
    verify_verification_code, send_verification_email
)
from ..middleware import hash_api_key, require_auth, check_rate_limit
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def generate_api_key() -> str:
    """Generate a secure API key using secrets module."""
    prefix = "mp_live_"
    key_length = 32
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(key_length))
    return f"{prefix}{key}"


def verify_dev_secret(request: Request):
    """Verify dev secret is provided. Dev endpoints require this header."""
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    
    dev_secret = request.headers.get("X-Dev-Secret", "")
    if not dev_secret or dev_secret != settings.dev_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing dev secret"
        )


@router.post("/register", response_model=RegistrationResponse)
async def register_bot(
    request: Request,
    reg_request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Start bot registration process - sends verification email."""
    # Rate limit registration
    check_rate_limit(request, settings.rate_limit_auth, prefix="register")
    
    # Check if bot name already exists
    existing_bot = db.query(Bot).filter(Bot.name == reg_request.bot_name).first()
    if existing_bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot name already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(Bot).filter(Bot.email == reg_request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check for existing pending registration
    existing_pending = db.query(PendingRegistration).filter(
        PendingRegistration.email == reg_request.email,
        PendingRegistration.verified == False,
        PendingRegistration.expires_at > datetime.utcnow()
    ).first()
    
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification email already sent. Please check your inbox or wait for it to expire."
        )
    
    # Generate verification code
    verification_code = generate_verification_code()
    hashed_code = hash_verification_code(verification_code)
    
    # Create pending registration
    pending = PendingRegistration(
        bot_name=reg_request.bot_name,
        email=reg_request.email,
        platform=reg_request.platform,
        description=reg_request.description,
        verification_code=hashed_code,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.verification_code_expiry_minutes)
    )
    
    db.add(pending)
    db.commit()
    db.refresh(pending)
    
    # Send verification email
    email_sent = await send_verification_email(
        reg_request.email, 
        verification_code, 
        reg_request.bot_name
    )
    
    if not email_sent:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )
    
    return RegistrationResponse(
        pending_id=pending.id,
        message=f"Verification code sent to {reg_request.email}. Code expires in {settings.verification_code_expiry_minutes} minutes."
    )


@router.post("/verify", response_model=VerificationResponse)
async def verify_registration(
    request: Request,
    verify_request: VerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify registration with 6-digit code. Max attempts enforced."""
    # Rate limit verification attempts
    check_rate_limit(request, settings.rate_limit_auth, prefix="verify")
    
    # Find pending registration
    pending = db.query(PendingRegistration).filter(
        PendingRegistration.id == verify_request.pending_id,
        PendingRegistration.verified == False
    ).first()
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending registration not found"
        )
    
    # Check if expired
    if pending.expires_at < datetime.utcnow():
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please register again."
        )
    
    # Check attempt count
    if hasattr(pending, 'attempts') and pending.attempts >= settings.verification_max_attempts:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please register again."
        )
    
    # Verify code
    if not verify_verification_code(verify_request.code, pending.verification_code):
        # Increment attempt counter
        if hasattr(pending, 'attempts'):
            pending.attempts = (pending.attempts or 0) + 1
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Check if bot names or email were taken while pending
    existing_bot_name = db.query(Bot).filter(Bot.name == pending.bot_name).first()
    existing_bot_email = db.query(Bot).filter(Bot.email == pending.email).first()
    
    if existing_bot_name:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot name was taken during verification. Please register again with a different name."
        )
    
    if existing_bot_email:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email was taken during verification. Please register again with a different email."
        )
    
    # Determine tier (first 30 get founder status)
    bot_count = db.query(Bot).count()
    tier = BotTier.FOUNDER if bot_count < settings.founder_bot_limit else BotTier.NEW
    
    # Generate API key
    api_key = generate_api_key()
    hashed_api_key = hash_api_key(api_key)
    
    # Create bot account
    bot = Bot(
        name=pending.bot_name,
        email=pending.email,
        api_key=hashed_api_key,
        tier=tier,
        description=pending.description,
        platform=pending.platform
    )
    
    db.add(bot)
    db.delete(pending)
    db.commit()
    db.refresh(bot)
    
    return VerificationResponse(
        api_key=api_key,
        bot_id=bot.id,
        tier=bot.tier,
        message=f"Registration successful! You are bot #{bot_count + 1}. " +
               ("Welcome, founder!" if tier == BotTier.FOUNDER else "Your edits will need approval until you gain trust.")
    )


# ── Dev-only Endpoints ──────────────────────────────────────────────────

@router.post("/dev/register")
async def dev_register_bot(
    request: Request,
    reg_request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """DEV ONLY: Register a bot instantly. Requires X-Dev-Secret header."""
    verify_dev_secret(request)
    
    if db.query(Bot).filter(Bot.name == reg_request.bot_name).first():
        raise HTTPException(status_code=400, detail="Bot name already registered")
    if db.query(Bot).filter(Bot.email == reg_request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    bot_count = db.query(Bot).count()
    tier = BotTier.FOUNDER if bot_count < settings.founder_bot_limit else BotTier.NEW
    
    api_key = generate_api_key()
    hashed_api_key = hash_api_key(api_key)
    
    bot = Bot(
        name=reg_request.bot_name,
        email=reg_request.email,
        api_key=hashed_api_key,
        tier=tier,
        description=reg_request.description,
        platform=reg_request.platform
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    
    return {
        "api_key": api_key,
        "bot_id": bot.id,
        "name": bot.name,
        "tier": bot.tier,
        "message": f"DEV registration successful! Bot #{bot_count + 1}. Tier: {tier}"
    }


@router.post("/dev/promote")
async def dev_promote_bot(
    request: Request,
    bot_id: int,
    tier: str,
    db: Session = Depends(get_db)
):
    """DEV ONLY: Promote a bot to any tier. Requires X-Dev-Secret header."""
    verify_dev_secret(request)
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        bot.tier = BotTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Valid: admin, founder, trusted, new")
    
    db.commit()
    return {"bot_id": bot.id, "name": bot.name, "tier": bot.tier}


# ── Authenticated Endpoints ─────────────────────────────────────────────

@router.get("/me", response_model=BotProfile)
async def get_bot_profile(
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current bot profile."""
    return current_bot


@router.post("/rotate-key")
async def rotate_api_key(
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Rotate API key. Returns new key, invalidates old one."""
    new_api_key = generate_api_key()
    current_bot.api_key = hash_api_key(new_api_key)
    db.commit()
    
    return {
        "api_key": new_api_key,
        "message": "API key rotated successfully. The old key is now invalid."
    }
