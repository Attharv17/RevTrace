import time
from fastapi import APIRouter
from pydantic import BaseModel

from app.db.database import ping_db
from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])
settings = get_settings()

_start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse, summary="API Health Check")
async def health_check() -> HealthResponse:
    """
    Returns the current health status of the API and its dependencies.

    - **status**: 'ok' or 'degraded'
    - **version**: current API version
    - **environment**: deployment environment
    - **database**: 'connected' or 'unreachable'
    - **uptime_seconds**: seconds since server start
    """
    db_ok = await ping_db()
    uptime = round(time.time() - _start_time, 2)

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=settings.version,
        environment=settings.environment,
        database="connected" if db_ok else "unreachable",
        uptime_seconds=uptime,
    )
