"""
LedgerPilot — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.dataset import router as dataset_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    print(f"[START] {settings.app_name} v{settings.version} starting up...")
    print(f"   Environment : {settings.environment}")
    print(f"   Database    : {settings.database_url.split('@')[-1]}")
    yield
    print("[STOP] Shutting down LedgerPilot API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered payment reconciliation backend.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(dataset_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/api/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
