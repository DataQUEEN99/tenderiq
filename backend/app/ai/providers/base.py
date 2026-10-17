import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
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
    elif provider in ("groq", "openai"):
        api_key = settings.groq_api_key or os.getenv("OPENAI_API_KEY", "")
        base_url = "https://api.groq.com/openai/v1" if provider == "groq" or settings.groq_api_key else None
        model = settings.groq_chat_model if (provider == "groq" or settings.groq_api_key) else "gpt-4o"
        max_tokens = kwargs.pop("max_tokens", 800)
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")