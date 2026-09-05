"""
RevTrace — FastAPI Application Entry Point
AI Revenue Recovery Engine
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.ingestion import router as ingestion_router
from app.api.opportunities import router as opportunities_router
from app.api.evaluation import router as evaluation_router
from app.api.assistant import router as assistant_router
from app.core.config import get_settings

settings = get_settings()

from app.db.session import engine
from app.models.base import Base
import app.models.financial   # noqa: F401 — registers financial tables
import app.models.opportunity  # noqa: F401 — registers recovery_opportunities table


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    print(f"[START] {settings.app_name} v{settings.version} starting up...")
    print(f"   Environment : {settings.environment}")
    print(f"   Database    : {settings.database_url.split('@')[-1]}")

    # Create all financial tables (idempotent via CREATE TABLE IF NOT EXISTS)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    print("[STOP] Shutting down RevTrace API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="RevTrace — AI Revenue Recovery Engine API.",
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
app.include_router(ingestion_router)
app.include_router(opportunities_router)
app.include_router(evaluation_router)
app.include_router(assistant_router)


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
