"""
RevTrace — Opportunities & Leakage API endpoints (Phase 4).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_session
from app.models.opportunity import RecoveryOpportunity
from app.schemas.opportunity import (
    LeakageRunStats,
    OpportunityListOut,
    OpportunityOut,
    OpportunitySummary,
    ScoringRunStats,
)
from app.services.leakage_engine import detect_leakage, get_opportunity_summary
from app.services.scoring_engine import run_scoring

router = APIRouter(tags=["Opportunities"])


# ── Leakage & Scoring triggers ───────────────────────────────────────────────

@router.post(
    "/api/leakage/run",
    response_model=LeakageRunStats,
    summary="Run leakage detection engine",
)
async def run_leakage_detection(session: AsyncSession = Depends(get_session)):
    """
    Scans all failed transactions and produces/updates RecoveryOpportunity records.
    Idempotent — safe to call multiple times.
    """
    try:
        return await detect_leakage(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leakage detection failed: {e}")


@router.post(
    "/api/scoring/run",
    response_model=ScoringRunStats,
    summary="Run recovery scoring engine",
)
async def run_scoring_engine(session: AsyncSession = Depends(get_session)):
    """
    Scores all opportunities deterministically.
    Idempotent — safe to call multiple times.
    """
    try:
        return await run_scoring(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring engine failed: {e}")


# ── Summary endpoint (must come before /{id} to avoid routing conflict) ──────

@router.get(
    "/api/opportunities/summary",
    response_model=OpportunitySummary,
    summary="Aggregate verified financial totals",
)
async def get_summary(session: AsyncSession = Depends(get_session)):
    """Returns verified aggregate totals — all values derived from real DB records."""
    summary = await get_opportunity_summary(session)
    return OpportunitySummary(**summary)


# ── List endpoint ─────────────────────────────────────────────────────────────

@router.get(
    "/api/opportunities",
    response_model=OpportunityListOut,
    summary="List recovery opportunities",
)
async def list_opportunities(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    reason: Optional[str] = Query(None, description="Filter by reason (partial match)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List recovery opportunities with optional filters. All figures are DB-verified."""
    query = select(RecoveryOpportunity)

    if status:
        query = query.where(RecoveryOpportunity.status == status.lower())
    if severity:
        query = query.where(RecoveryOpportunity.severity == severity.upper())
    if reason:
        query = query.where(RecoveryOpportunity.reason.ilike(f"%{reason}%"))

    # Total count
    count_result = await session.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Paginated results — ordered by revenue_at_risk descending
    offset = (page - 1) * page_size
    paginated = query.order_by(RecoveryOpportunity.revenue_at_risk.desc()).offset(offset).limit(page_size)
    result = await session.execute(paginated)
    items = result.scalars().all()

    return OpportunityListOut(
        items=[OpportunityOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Detail endpoint ───────────────────────────────────────────────────────────

@router.get(
    "/api/opportunities/{opportunity_id}",
    response_model=OpportunityOut,
    summary="Get opportunity by ID",
)
async def get_opportunity(
    opportunity_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(RecoveryOpportunity).where(RecoveryOpportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
    return OpportunityOut.model_validate(opp)
