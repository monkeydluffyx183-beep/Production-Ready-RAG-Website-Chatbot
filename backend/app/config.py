from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "gemini-2.5-flash"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    max_pages: int = 50
    request_timeout: int = 15
    user_agent: str = "Mozilla/5.0 (compatible; RAGBot/1.0)"

    chroma_persist_dir: str = "./chroma_data"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
