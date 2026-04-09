import litellm
import traceback
from loguru import logger
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

litellm.set_verbose = False
# Setup API keys so LiteLLM can find them if they exist
import os
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

async def call_llm(prompt: str, system_prompt: str = "Você é um assistente útil e objetivo.") -> Optional[str]:
    """
    Standard LLM call with fallback mechanism.
    Attempts default provider (Ollama) first, then fallback (Gemini), then None (leads to static rules).
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # 1. Try Default Provider
    try:
        model = settings.default_llm_model
        if settings.default_llm_provider == "ollama":
            model = f"ollama_chat/{settings.default_llm_model}"
        elif settings.default_llm_provider == "gemini":
            model = f"gemini/{settings.default_llm_model}"
            
        logger.info(f"LLM Client: Attempting default ({model})")
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            api_base=settings.ollama_base_url if settings.default_llm_provider == "ollama" else None,
            max_tokens=2048
        )
        return response.choices[0].message.content
        
    except Exception as e:
        logger.warning(f"Default LLM failed: {e}")
        
    # 2. Try Fallback Provider
    if settings.fallback_llm_provider and settings.fallback_llm_model:
        try:
            model = settings.fallback_llm_model
            if settings.fallback_llm_provider == "gemini":
                model = f"gemini/{settings.fallback_llm_model}"
                if not settings.gemini_api_key:
                    logger.warning("Gemini skipped: No API key provided in .env")
                    return None
            elif settings.fallback_llm_provider == "ollama":
                model = f"ollama_chat/{settings.fallback_llm_model}"
                    
            logger.info(f"LLM Client: Attempting fallback ({model})")
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                max_tokens=2048
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Fallback LLM failed: {e}")
            
    # 3. Failed all
    logger.error("All LLM providers failed. Returning None.")
    return None
