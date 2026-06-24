import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RAG Chatbot"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./rag_chatbot.db"
    
    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # LLM
    LLM_PROVIDER: str = "gemini"  # or "openai"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 4
    SCORE_THRESHOLD: float = 0.5
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
