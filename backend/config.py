import os
import secrets
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "order_system"
    
    # Security key - MUST set via environment variable in production
    SECRET_KEY: str = ""
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 5242880
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5174"
    
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    
    ENABLE_DOCS: bool = True
    
    model_config = {"env_file": ".env"}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
            print("WARNING: SECRET_KEY not set, generated temporary key.")
        if os.getenv("SECRET_KEY"):
            self.SECRET_KEY = os.getenv("SECRET_KEY")
        if os.getenv("CORS_ORIGINS"):
            self.CORS_ORIGINS = os.getenv("CORS_ORIGINS")
        if os.getenv("DB_POOL_SIZE"):
            self.DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE"))
        if os.getenv("DB_MAX_OVERFLOW"):
            self.DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW"))
        if os.getenv("DB_POOL_RECYCLE"):
            self.DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE"))
        if os.getenv("ENABLE_DOCS"):
            self.ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    
    @property
    def cors_origins_list(self) -> List[str]:
       return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
