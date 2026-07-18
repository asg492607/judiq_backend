import os
from functools import lru_cache
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    PROJECT_NAME: str = "JudiQ Legal AI"
    VERSION: str = "12.5.0-ENTERPRISE"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme_secure_key_for_dev_only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8          
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
    BACKEND_CORS_ORIGINS: list = [
        "https://judiq.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ]
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "c2VjcmV0X2tleV90aGF0X2lzX2V4YWN0bHlfMzJfYnk=")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
@lru_cache()
def get_settings():
    s = Settings()
    if len(s.ENCRYPTION_KEY) not in (43, 44) or " " in s.ENCRYPTION_KEY:
        if not s.DEBUG:
            raise ValueError("ENCRYPTION_KEY must be a valid 32-byte base64 string in production.")
        s.ENCRYPTION_KEY = "c2VjcmV0X2tleV90aGF0X2lzX2V4YWN0bHlfMzJfYnk="
    if not s.DEBUG and s.SECRET_KEY == "changeme_secure_key_for_dev_only":
        import logging
        logging.getLogger("config").warning("WARNING: SECRET_KEY is set to default in production. Please set a custom SECRET_KEY env var for security.")
    return s
settings = get_settings()
