# pyrefly: ignore [missing-import]
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JudiQ Legal AI"
    VERSION: str = "12.5.0-ENTERPRISE"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7d9b9c9d9e9f90919293949596979899")
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
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "G-o6dGqzB2H7r7C4Uv6hM3_bT4-Y3PZ9N4e4Wv4Y-xY=")
    
    # Feature Flags
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()
