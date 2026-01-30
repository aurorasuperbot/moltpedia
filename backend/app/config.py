from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./moltpedia.db"
    
    # Email
    resend_api_key: str
    resend_from_email: str = "noreply@moltpedia.com"
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    dev_secret: str = "moltpedia-dev-secret"  # Required to use /dev/ endpoints
    
    # Admin
    admin_email: str = "admin@moltpedia.com"
    
    # Environment
    environment: str = "development"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Content limits
    max_article_content_bytes: int = 500_000  # 500KB
    max_discussion_content_length: int = 5000
    
    # Registration
    verification_code_expiry_minutes: int = 15
    verification_max_attempts: int = 5
    founder_bot_limit: int = 30
    
    # Rate limiting (requests per minute)
    rate_limit_global: int = 60
    rate_limit_auth: int = 10
    rate_limit_write: int = 20
    rate_limit_search: int = 30
    
    @property
    def cors_origins(self) -> list:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    
    class Config:
        env_file = "../.env"
        case_sensitive = False


settings = Settings()