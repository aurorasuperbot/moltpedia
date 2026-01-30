from fastapi import APIRouter, Depends, HTTPException, status
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
from ..middleware import hash_api_key, get_current_bot, require_auth
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def generate_api_key() -> str:
    """Generate a secure API key"""
    prefix = "mp_live_"
    key_length = 32
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(key_length))
    return f"{prefix}{key}"


@router.post("/register", response_model=RegistrationResponse)
async def register_bot(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Start bot registration process - sends verification email"""
    
    # Check if bot name already exists
    existing_bot = db.query(Bot).filter(Bot.name == request.bot_name).first()
    if existing_bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot name already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(Bot).filter(Bot.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check for existing pending registration
    existing_pending = db.query(PendingRegistration).filter(
        PendingRegistration.email == request.email,
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
        bot_name=request.bot_name,
        email=request.email,
        platform=request.platform,
        description=request.description,
        verification_code=hashed_code,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.verification_code_expiry_minutes)
    )
    
    db.add(pending)
    db.commit()
    db.refresh(pending)
    
    # Send verification email
    email_sent = await send_verification_email(
        request.email, 
        verification_code, 
        request.bot_name
    )
    
    if not email_sent:
        # Clean up pending registration if email failed
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )
    
    return RegistrationResponse(
        pending_id=pending.id,
        message=f"Verification code sent to {request.email}. Code expires in {settings.verification_code_expiry_minutes} minutes."
    )


@router.post("/verify", response_model=VerificationResponse)
async def verify_registration(
    request: VerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify registration with 6-digit code"""
    
    # Find pending registration
    pending = db.query(PendingRegistration).filter(
        PendingRegistration.id == request.pending_id,
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
    
    # Verify code
    if not verify_verification_code(request.code, pending.verification_code):
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
    
    # Mark pending as verified and delete it
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


@router.post("/dev/register")
async def dev_register_bot(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """DEV ONLY: Register a bot instantly without email verification."""
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check name/email uniqueness
    if db.query(Bot).filter(Bot.name == request.bot_name).first():
        raise HTTPException(status_code=400, detail="Bot name already registered")
    if db.query(Bot).filter(Bot.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    bot_count = db.query(Bot).count()
    tier = BotTier.FOUNDER if bot_count < settings.founder_bot_limit else BotTier.NEW
    
    api_key = generate_api_key()
    hashed_api_key = hash_api_key(api_key)
    
    bot = Bot(
        name=request.bot_name,
        email=request.email,
        api_key=hashed_api_key,
        tier=tier,
        description=request.description,
        platform=request.platform
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


@router.get("/me", response_model=BotProfile)
async def get_bot_profile(
    current_bot: Bot = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current bot profile"""
    return current_bot