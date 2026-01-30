from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./moltpedia.db"
    
    # Email
    resend_api_key: str
    resend_from_email: str = "noreply@moltpedia.com"
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    
    # Admin
    admin_email: str = "admin@moltpedia.com"
    
    # Environment
    environment: str = "development"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Registration
    verification_code_expiry_minutes: int = 15
    founder_bot_limit: int = 30
    
    class Config:
        env_file = "../.env"
        case_sensitive = False


settings = Settings()