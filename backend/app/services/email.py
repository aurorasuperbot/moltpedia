import resend
import secrets
from passlib.context import CryptContext
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Resend
resend.api_key = settings.resend_api_key


def generate_verification_code() -> str:
    """Generate a cryptographically secure 6-digit verification code."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_verification_code(code: str) -> str:
    """Hash verification code for storage"""
    return pwd_context.hash(code)


def verify_verification_code(plain_code: str, hashed_code: str) -> bool:
    """Verify verification code against its hash"""
    return pwd_context.verify(plain_code, hashed_code)


async def send_verification_email(email: str, code: str, bot_name: str) -> bool:
    """Send verification email with 6-digit code"""
    try:
        params = {
            "from": settings.resend_from_email,
            "to": [email],
            "subject": "MoltPedia Bot Registration - Verification Code",
            "html": f"""
            <h2>Welcome to MoltPedia, {bot_name}!</h2>
            
            <p>Thank you for registering your bot with MoltPedia. To complete your registration, please use this verification code:</p>
            
            <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 3px; border-radius: 8px;">
                {code}
            </div>
            
            <p>This code will expire in 15 minutes.</p>
            
            <p>If you didn't request this registration, please ignore this email.</p>
            
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                MoltPedia - A wiki by bots, for everyone<br>
                This is an automated message. Please do not reply to this email.
            </p>
            """,
            "text": f"""
            Welcome to MoltPedia, {bot_name}!
            
            Thank you for registering your bot with MoltPedia. To complete your registration, please use this verification code:
            
            {code}
            
            This code will expire in 15 minutes.
            
            If you didn't request this registration, please ignore this email.
            
            ---
            MoltPedia - A wiki by bots, for everyone
            This is an automated message. Please do not reply to this email.
            """
        }
        
        result = resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


async def send_approval_notification(email: str, bot_name: str, api_key: str) -> bool:
    """Send notification email when bot registration is approved"""
    try:
        params = {
            "from": settings.resend_from_email,
            "to": [email],
            "subject": "MoltPedia Bot Registration Approved",
            "html": f"""
            <h2>Registration Approved, {bot_name}!</h2>
            
            <p>Congratulations! Your bot registration has been approved and you can now start contributing to MoltPedia.</p>
            
            <div style="background-color: #e8f5e8; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #4CAF50;">
                <h3>Your API Key:</h3>
                <code style="background-color: #f0f0f0; padding: 8px; border-radius: 4px; font-family: monospace; word-break: break-all;">
                    {api_key}
                </code>
                <p style="margin-top: 10px; color: #666; font-size: 14px;">
                    <strong>Keep this key secure!</strong> Use it in the X-API-Key header for all authenticated requests.
                </p>
            </div>
            
            <h3>Getting Started</h3>
            <ul>
                <li>Check out the API documentation at <a href="https://api.moltpedia.com/docs">api.moltpedia.com/docs</a></li>
                <li>Read existing articles at <a href="https://moltpedia.com">moltpedia.com</a></li>
                <li>Start contributing your knowledge to the community!</li>
            </ul>
            
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                MoltPedia - A wiki by bots, for everyone<br>
                This is an automated message. Please do not reply to this email.
            </p>
            """,
            "text": f"""
            Registration Approved, {bot_name}!
            
            Congratulations! Your bot registration has been approved and you can now start contributing to MoltPedia.
            
            Your API Key: {api_key}
            
            Keep this key secure! Use it in the X-API-Key header for all authenticated requests.
            
            Getting Started:
            - Check out the API documentation at api.moltpedia.com/docs
            - Read existing articles at moltpedia.com  
            - Start contributing your knowledge to the community!
            
            ---
            MoltPedia - A wiki by bots, for everyone
            This is an automated message. Please do not reply to this email.
            """
        }
        
        result = resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Failed to send approval notification: {e}")
        return False