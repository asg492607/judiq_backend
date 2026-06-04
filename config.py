# pyrefly: ignore [missing-import]
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JudiQ Legal AI"
    VERSION: str = "12.5.0-ENTERPRISE"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme_secure_key_for_dev_only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "https://judiq.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    
    # Encryption (Fernet key must be 32 url-safe base64-encoded bytes)
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "c2VjcmV0X2tleV90aGF0X2lzX2V4YWN0bHlfMzJfYnl0ZXM=")
    
    # Feature Flags
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

@lru_cache()
def get_settings():
    s = Settings()
    # Validate the fernet key (must be 43 or 44 chars base64 of 32 bytes)
    if len(s.ENCRYPTION_KEY) not in (43, 44) or " " in s.ENCRYPTION_KEY:
        s.ENCRYPTION_KEY = "c2VjcmV0X2tleV90aGF0X2lzX2V4YWN0bHlfMzJfYnl0ZXM="
    return s

settings = get_settings()
