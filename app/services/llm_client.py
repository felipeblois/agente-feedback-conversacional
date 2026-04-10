import os
from typing import Optional

import litellm
from loguru import logger

from app.core.config import get_settings


settings = get_settings()

litellm.set_verbose = False

if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key


def _resolve_model(provider: str, model: str) -> str:
    if provider == "gemini":
        return f"gemini/{model}"
    if provider == "anthropic":
        return f"anthropic/{model}"
    if provider == "openai":
        return f"openai/{model}"
    return model


def _provider_ready(provider: str) -> bool:
    if provider == "gemini":
        return bool(settings.gemini_api_key)
    if provider == "anthropic":
        return bool(settings.anthropic_api_key)
    if provider == "openai":
        return bool(settings.openai_api_key)
    return False


async def _call_provider(provider: str, model: str, messages) -> Optional[str]:
    if not _provider_ready(provider):
        logger.warning(f"{provider.title()} skipped: missing API key in .env")
        return None

    full_model = _resolve_model(provider, model)
    logger.info(f"LLM Client: Attempting {provider} ({full_model})")
    response = await litellm.acompletion(
        model=full_model,
        messages=messages,
        max_tokens=2048,
    )
    return response.choices[0].message.content


async def call_llm(
    prompt: str,
    system_prompt: str = "Voce e um assistente util e objetivo.",
) -> Optional[str]:
    """
    Standard LLM call with cloud fallback.
    Attempts Gemini first, then Anthropic, then returns None for static fallback.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    providers = [
        (settings.default_llm_provider, settings.default_llm_model, "default"),
        (settings.fallback_llm_provider, settings.fallback_llm_model, "fallback"),
    ]

    for provider, model, label in providers:
        if not provider or not model:
            continue
        try:
            content = await _call_provider(provider, model, messages)
            if content:
                return content
        except Exception as exc:
            logger.warning(f"{label.title()} LLM failed ({provider}/{model}): {exc}")

    logger.error("All cloud LLM providers failed. Returning None.")
    return None
