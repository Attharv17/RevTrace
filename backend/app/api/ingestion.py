"""
RevTrace — Ingestion API endpoints (Phase 3).
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.ingestion import DatabaseStats, IngestionStats
from app.services.ingestion_service import get_database_stats, ingest_csv_batch

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])

# Default dataset path (relative to backend directory)
DEFAULT_DATASET_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "revtrace_payments.csv")


@router.post("/run", response_model=IngestionStats, summary="Run ingestion")
async def run_ingestion(
    dataset_path: str = DEFAULT_DATASET_PATH,
    session: AsyncSession = Depends(get_session),
):
    """
    Ingest the synthetic payment dataset CSV into PostgreSQL.
    Safe to call multiple times — duplicates are silently skipped.
    """
    try:
        stats = await ingest_csv_batch(dataset_path, session)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.get("/stats", response_model=DatabaseStats, summary="Database row counts")
async def ingestion_stats(session: AsyncSession = Depends(get_session)):
    """Returns current row counts across all financial tables."""
    counts = await get_database_stats(session)
    return DatabaseStats(**counts)
