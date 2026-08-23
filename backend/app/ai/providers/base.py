from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import get_settings


def get_llm(provider: str = None, temperature: float = 0.2, **kwargs) -> BaseChatModel:
    settings = get_settings()
    provider = provider or settings.llm_provider

    if provider == "ollama":
        return ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
            **kwargs
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.gemini_api_key,
            temperature=temperature,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")