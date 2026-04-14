from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import os
import time

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.observability import log_event, observability_service

settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.app_name,
    description="Agent for collecting conversational feedback",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    status_code = 500
    error_message = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        error_message = exc.__class__.__name__
        raise
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        observability_service.record_http(
            route=route_path,
            method=request.method,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error_message,
        )
        level = "warning" if status_code >= 400 or error_message else "info"
        log_event(
            level,
            "http_request_completed",
            method=request.method,
            path=route_path,
            status_code=status_code,
            duration_ms=duration_ms,
            client=getattr(request.client, "host", "unknown"),
            error=error_message,
        )

# Ensure static directory exists before mounting
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from app.api.routes import health, sessions, responses, analysis, exports, settings as settings_routes
from app.api.routes import public

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(responses.router, prefix="/api/v1/public", tags=["participant flow"])
app.include_router(analysis.router, prefix="/api/v1/sessions", tags=["analysis"])
app.include_router(exports.router, prefix="/api/v1/sessions", tags=["exports"])
app.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(public.router, prefix="/f", tags=["public template"])
