from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    openai_api_key: str
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "rag_documents"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    chunk_size: int = 800
    chunk_overlap: int = 100
    relevance_threshold: float = -0.5
    allow_general_knowledge: bool = True
    wikipedia_enabled: bool = True

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_chroma_persist_dir() -> Path:
    configured_path = Path(get_settings().chroma_persist_dir)
    return configured_path if configured_path.is_absolute() else BACKEND_DIR / configured_path


def get_collection_name() -> str:
    return get_settings().chroma_collection_name
