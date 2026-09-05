"""
RevTrace — Pydantic schemas for Recovery Opportunities (Phase 4).
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class OpportunityOut(BaseModel):
    """Single recovery opportunity response — all figures are DB-verified."""
    id: int
    transaction_id: str
    expected_revenue: float
    realized_revenue: float
    revenue_at_risk: float
    recoverable_amount: float
    reason: str
    severity: str   # LOW | MEDIUM | HIGH | CRITICAL
    status: str     # pending | in_progress | recovered | unrecoverable
    
    # Phase 5: Scoring fields
    recovery_probability: Optional[float] = None
    expected_recovery: Optional[float] = None
    priority: Optional[str] = None
    recommended_action: Optional[str] = None
    decision_band: Optional[str] = None
    score_version: Optional[str] = None
    score_metadata: Optional[str] = None
    scored_at: Optional[datetime] = None

    detected_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunityListOut(BaseModel):
    """Paginated list of opportunities."""
    items: List[OpportunityOut]
    total: int
    page: int
    page_size: int


class OpportunitySummary(BaseModel):
    """
    Aggregate verified financial totals.
    All values derived from real database records — not estimated.
    """
    total_opportunities: int
    total_revenue_at_risk: float
    total_realized_revenue: float
    total_expected_revenue: float
    total_recoverable_amount: float

    # Breakdown by status
    pending_count: int
    in_progress_count: int
    recovered_count: int
    unrecoverable_count: int

    # Breakdown by severity
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class LeakageRunStats(BaseModel):
    """Result returned after running the leakage detection engine."""
    transactions_scanned: int
    opportunities_created: int
    opportunities_updated: int
    skipped_not_applicable: int
    duration_seconds: float


class ScoringRunStats(BaseModel):
    """Result returned after running the recovery scoring engine."""
    opportunities_scanned: int
    opportunities_scored: int
    duration_seconds: float
