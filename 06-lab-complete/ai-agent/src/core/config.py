import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env if it exists
load_dotenv()

class Settings(BaseSettings):
    # API info
    APP_NAME: str = "Smart Travel Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field("development", alias="ENVIRONMENT")
    
    # LLM keys
    GEMINI_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gemini-2.0-flash"
    TEMPERATURE: float = 0.1
    
    # Tool keys
    TAVILY_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY: Optional[str] = None
    EXCHANGERATE_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None
    RAPIDAPI_KEY: Optional[str] = None
    
    # App specific
    USE_TOOLS: bool = True
    DATABASE_URL: str = "sqlite:///./checkpoints.sqlite"
    REDIS_URL: Optional[str] = None
    
    # Security
    AGENT_API_KEY: str = "dev-key-12345"
    JWT_SECRET: str = "dev-jwt-secret-replace-me-in-prod"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()