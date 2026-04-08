from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Agent for collecting conversational feedback",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists before mounting
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from app.api.routes import health, sessions, responses, analysis, exports
from app.api.routes import public

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(responses.router, prefix="/api/v1/public", tags=["participant flow"])
app.include_router(analysis.router, prefix="/api/v1/sessions", tags=["analysis"])
app.include_router(exports.router, prefix="/api/v1/sessions", tags=["exports"])
app.include_router(public.router, prefix="/f", tags=["public template"])
