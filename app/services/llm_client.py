import os
import time
from typing import Dict, Optional, Tuple

import litellm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.observability import log_event, observability_service
from app.services.settings_service import settings_service


settings = get_settings()

litellm.set_verbose = False


SUPPORTED_PROVIDERS = {"gemini", "anthropic", "openai"}


def _resolve_model(provider: str, model: str) -> str:
    if provider == "gemini":
        return f"gemini/{model}"
    if provider == "anthropic":
        return f"anthropic/{model}"
    if provider == "openai":
        return f"openai/{model}"
    return model


def _set_provider_env(runtime_config: Dict[str, str]) -> None:
    if runtime_config.get("gemini_api_key"):
        os.environ["GEMINI_API_KEY"] = runtime_config["gemini_api_key"]
    if runtime_config.get("anthropic_api_key"):
        os.environ["ANTHROPIC_API_KEY"] = runtime_config["anthropic_api_key"]
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key


def _provider_ready(provider: str, runtime_config: Dict[str, str]) -> Tuple[bool, str]:
    if provider not in SUPPORTED_PROVIDERS:
        return False, "provider_not_supported"
    if provider == "gemini" and not runtime_config.get("gemini_api_key"):
        return False, "provider_not_configured"
    if provider == "anthropic" and not runtime_config.get("anthropic_api_key"):
        return False, "provider_not_configured"
    if provider == "openai" and not settings.openai_api_key:
        return False, "provider_not_configured"
    return True, "ready"


def _classify_exception(exc: Exception) -> Tuple[str, str]:
    text = str(exc)
    lowered = text.lower()

    if "429" in lowered or "resource_exhausted" in lowered or "quota" in lowered:
        return "rate_limit", "Quota excedida ou limite de uso atingido"
    if "503" in lowered or "serviceunavailable" in lowered or "unavailable" in lowered:
        return "service_unavailable", "Modelo temporariamente indisponivel"
    if "401" in lowered or "403" in lowered or "auth" in lowered or "api key" in lowered:
        return "auth_error", "Falha de autenticacao ou chave invalida"
    if "connection" in lowered or "timeout" in lowered or "connect" in lowered:
        return "connection_error", "Falha de conexao com o provedor"
    return "unknown_error", text.splitlines()[0][:180]


def _log_attempt(stage: str, provider: str, model: str, credential_source: str) -> None:
    log_event(
        "info",
        "llm_attempt",
        stage=stage,
        provider=provider,
        model=model,
        credential_source=credential_source,
    )


def _log_skip(stage: str, provider: str, model: str, category: str, message: str) -> None:
    log_event(
        "warning",
        "llm_skipped",
        stage=stage,
        provider=provider,
        model=model,
        category=category,
        message=message,
    )


def _log_failure(stage: str, provider: str, model: str, category: str, message: str, action: str) -> None:
    log_event(
        "warning",
        "llm_failed",
        stage=stage,
        provider=provider,
        model=model,
        category=category,
        message=message,
        action=action,
    )


async def _call_provider(
    stage: str,
    provider: str,
    model: str,
    messages,
    runtime_config: Dict[str, str],
) -> Optional[str]:
    ready, category = _provider_ready(provider, runtime_config)
    if not ready:
        message = (
            "Provider nao configurado para esta instancia"
            if category == "provider_not_configured"
            else "Provider nao suportado pela estrategia atual"
        )
        _log_skip(stage, provider, model, category, message)
        return None

    full_model = _resolve_model(provider, model)
    _log_attempt(stage, provider, full_model, runtime_config.get("credential_source", "platform"))
    started_at = time.perf_counter()
    try:
        response = await litellm.acompletion(
            model=full_model,
            messages=messages,
            max_tokens=2048,
        )
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        observability_service.record_llm(
            provider=provider,
            model=model,
            stage=stage,
            duration_ms=duration_ms,
            success=True,
        )
        log_event(
            "info",
            "llm_provider_completed",
            stage=stage,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
        )
        return response.choices[0].message.content
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        category, _ = _classify_exception(exc)
        observability_service.record_llm(
            provider=provider,
            model=model,
            stage=stage,
            duration_ms=duration_ms,
            success=False,
            error_category=category,
        )
        raise


async def _load_runtime_config(db: AsyncSession) -> Dict[str, str]:
    runtime_config = await settings_service.get_runtime_config(db)
    _set_provider_env(runtime_config)
    return runtime_config


async def call_llm(
    db: AsyncSession,
    prompt: str,
    system_prompt: str = "Voce e um assistente util e objetivo.",
    provider_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> Optional[str]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    runtime_config = await _load_runtime_config(db)

    providers = [
        (
            provider_override or runtime_config["default_provider"],
            model_override or runtime_config["default_model"],
            "default",
        ),
        (
            runtime_config["fallback_provider"],
            runtime_config["fallback_model"],
            "fallback",
        ),
    ]

    if provider_override:
        providers = [(provider_override, model_override or runtime_config["default_model"], "selected")]

    for index, (provider, model, stage) in enumerate(providers):
        if not provider or not model:
            continue

        next_action = "trying_fallback" if index < len(providers) - 1 else "using_static_fallback"

        try:
            content = await _call_provider(stage, provider, model, messages, runtime_config)
            if content:
                log_event(
                    "info",
                    "llm_success",
                    stage=stage,
                    provider=provider,
                    model=model,
                    credential_source=runtime_config.get("credential_source", "platform"),
                )
                return content
        except Exception as exc:
            category, message = _classify_exception(exc)
            _log_failure(stage, provider, model, category, message, next_action)

    log_event(
        "error",
        "llm_fallback_engaged",
        provider="jarvis",
        reason="all_cloud_providers_failed",
    )
    return None


async def test_provider_connection(
    db: AsyncSession,
    provider: str,
    model: Optional[str] = None,
) -> Dict[str, str]:
    runtime_config = await _load_runtime_config(db)

    if provider == "gemini":
        selected_model = model or runtime_config["default_model"]
    elif provider == "anthropic":
        selected_model = model or runtime_config["fallback_model"]
    else:
        selected_model = model or "n/a"

    prompt = "Responda apenas com a palavra: CONECTADO"
    response = await call_llm(
        db,
        prompt,
        "Voce e um validador tecnico. Responda apenas CONECTADO.",
        provider_override=provider,
        model_override=selected_model if provider in SUPPORTED_PROVIDERS else None,
    )
    success = bool(response and "CONECTADO" in response.upper())

    return {
        "success": success,
        "provider": provider,
        "model": selected_model,
        "credential_source": runtime_config.get("credential_source", "platform"),
        "message": "Conexao validada com sucesso." if success else "Nao foi possivel validar a conexao.",
    }
