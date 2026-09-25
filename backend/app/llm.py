from functools import lru_cache

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import get_settings


@lru_cache
def get_chat_model():
    settings = get_settings()
    if settings.model_provider == "ollama":
        return ChatOllama(
            model=settings.chat_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )


@lru_cache
def get_embedding_model():
    settings = get_settings()
    if settings.model_provider == "ollama":
        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )