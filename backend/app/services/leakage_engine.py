"""
RevTrace — Revenue Leakage Detection Engine (Phase 4).

Deterministic rules engine. All financial values are derived from verified
database records in the `transactions` and `payment_attempts` tables.
No values are invented or estimated.

Financial definitions:
  expected_revenue  = transaction.amount
  realized_revenue  = sum of recovered_amount from successful PaymentAttempts
  revenue_at_risk   = max(expected_revenue - realized_revenue, 0)  — never negative
  recoverable_amount = ground_truth_recovered_amount (labelled as ground truth)
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.financial import PaymentAttempt, Transaction
from app.models.opportunity import RecoveryOpportunity
from app.schemas.opportunity import LeakageRunStats

logger = logging.getLogger(__name__)

_IS_POSTGRES = "postgresql" in str(engine.url)

# Failure reasons that indicate revenue leakage
LEAKAGE_FAILURE_REASONS = {
    "timeout",
    "insufficient_funds",
    "card_blocked_or_stolen",
    "user_abandoned",
    "link_expired",
    "mandate_failed",
}

# Human-readable reason labels
REASON_LABELS = {
    "timeout":               "Payment Timeout",
    "insufficient_funds":    "Insufficient Funds",
    "card_blocked_or_stolen": "Hard Decline",
    "user_abandoned":        "Abandoned Checkout",
    "link_expired":          "Expired Payment Link",
    "mandate_failed":        "Recurring Mandate Failure",
}


# ── Financial helpers (pure functions — fully testable) ──────────────────────

def compute_realized_revenue(attempt_outcomes: list[tuple[str, float]]) -> float:
    """
    Sum recovered_amount from attempts where outcome is 'success' or 'partial'.
    Only actual collections count; pending/failed attempts contribute zero.
    """
    total = sum(
        amt for outcome, amt in attempt_outcomes
        if outcome in ("success", "partial")
    )
    return round(total, 2)


def compute_revenue_at_risk(expected: float, realized: float) -> float:
    """revenue_at_risk = max(expected - realized, 0). Never negative."""
    return round(max(expected - realized, 0.0), 2)


def compute_severity(revenue_at_risk: float) -> str:
    if revenue_at_risk > 25_000:
        return "CRITICAL"
    if revenue_at_risk > 10_000:
        return "HIGH"
    if revenue_at_risk > 2_500:
        return "MEDIUM"
    return "LOW"


def compute_status(
    ground_truth_recoverable: bool,
    attempt_outcomes: list[tuple[str, float]],
) -> str:
    if not ground_truth_recoverable:
        return "unrecoverable"
    outcomes = {o for o, _ in attempt_outcomes}
    if "success" in outcomes:
        return "recovered"
    if "pending" in outcomes or "in_progress" in outcomes:
        return "in_progress"
    return "pending"


# ── Upsert helper ────────────────────────────────────────────────────────────

async def _upsert_opportunity(
    session: AsyncSession,
    values: dict,
) -> tuple[bool, bool]:
    """
    Insert or update a RecoveryOpportunity by transaction_id.
    Returns (created, updated).
    """
    # Check if opportunity already exists
    result = await session.execute(
        select(RecoveryOpportunity.id).where(
            RecoveryOpportunity.transaction_id == values["transaction_id"]
        )
    )
    existing_id = result.scalar_one_or_none()

    if existing_id is None:
        # Insert new
        if _IS_POSTGRES:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = (
                pg_insert(RecoveryOpportunity)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["transaction_id"],
                    set_={k: v for k, v in values.items() if k != "transaction_id"},
                )
            )
        else:
            stmt = sqlite_insert(RecoveryOpportunity).values(**values).prefix_with("OR REPLACE")
        await session.execute(stmt)
        return True, False
    else:
        # Update existing (recalculated figures)
        from sqlalchemy import update as sa_update
        stmt = (
            sa_update(RecoveryOpportunity)
            .where(RecoveryOpportunity.id == existing_id)
            .values(**{k: v for k, v in values.items() if k != "transaction_id"})
        )
        await session.execute(stmt)
        return False, True


# ── Core engine ──────────────────────────────────────────────────────────────

async def detect_leakage(session: AsyncSession) -> LeakageRunStats:
    """
    Scan all failed transactions and produce/update RecoveryOpportunity rows.
    Idempotent — safe to run multiple times on the same data.
    """
    t_start = time.perf_counter()

    transactions_scanned = 0
    opportunities_created = 0
    opportunities_updated = 0
    skipped_not_applicable = 0

    # Query all transactions (we check payment_status in Python for testability)
    result = await session.execute(select(Transaction))
    transactions = result.scalars().all()

    for txn in transactions:
        transactions_scanned += 1

        # Skip successful payments — no leakage
        if txn.payment_status != "failed":
            skipped_not_applicable += 1
            continue

        # Skip failure reasons outside our leakage scope
        failure_reason = (txn.failure_reason or "").lower().strip()
        if failure_reason not in LEAKAGE_FAILURE_REASONS:
            skipped_not_applicable += 1
            continue

        # Fetch linked payment attempts
        attempts_result = await session.execute(
            select(PaymentAttempt.recovery_outcome, PaymentAttempt.recovered_amount)
            .where(PaymentAttempt.transaction_id == txn.transaction_id)
        )
        attempt_outcomes = [(row.recovery_outcome, row.recovered_amount) for row in attempts_result]

        # Compute all financial fields deterministically
        expected_revenue = round(txn.amount, 2)
        realized_revenue = compute_realized_revenue(attempt_outcomes)
        revenue_at_risk = compute_revenue_at_risk(expected_revenue, realized_revenue)
        recoverable_amount = round(txn.ground_truth_recovered_amount, 2)
        reason = REASON_LABELS.get(failure_reason, failure_reason)
        severity = compute_severity(revenue_at_risk)
        status = compute_status(txn.ground_truth_recoverable, attempt_outcomes)

        values = {
            "transaction_id":    txn.transaction_id,
            "expected_revenue":  expected_revenue,
            "realized_revenue":  realized_revenue,
            "revenue_at_risk":   revenue_at_risk,
            "recoverable_amount": recoverable_amount,
            "reason":            reason,
            "severity":          severity,
            "status":            status,
        }

        created, updated = await _upsert_opportunity(session, values)
        if created:
            opportunities_created += 1
        elif updated:
            opportunities_updated += 1

    await session.commit()
    duration = round(time.perf_counter() - t_start, 3)

    logger.info(
        "Leakage detection complete: %d scanned, %d created, %d updated, %d skipped in %.2fs",
        transactions_scanned, opportunities_created, opportunities_updated,
        skipped_not_applicable, duration,
    )

    return LeakageRunStats(
        transactions_scanned=transactions_scanned,
        opportunities_created=opportunities_created,
        opportunities_updated=opportunities_updated,
        skipped_not_applicable=skipped_not_applicable,
        duration_seconds=duration,
    )


# ── Summary query ────────────────────────────────────────────────────────────

async def get_opportunity_summary(session: AsyncSession) -> dict:
    """Aggregate verified financial totals from the recovery_opportunities table."""
    result = await session.execute(
        select(
            func.count(RecoveryOpportunity.id),
            func.sum(RecoveryOpportunity.revenue_at_risk),
            func.sum(RecoveryOpportunity.realized_revenue),
            func.sum(RecoveryOpportunity.expected_revenue),
            func.sum(RecoveryOpportunity.recoverable_amount),
        )
    )
    row = result.one()
    total, at_risk, realized, expected, recoverable = row

    def _count_where(**kwargs):
        return session.execute(
            select(func.count(RecoveryOpportunity.id)).filter_by(**kwargs)
        )

    pending_r       = await _count_where(status="pending")
    in_progress_r   = await _count_where(status="in_progress")
    recovered_r     = await _count_where(status="recovered")
    unrecoverable_r = await _count_where(status="unrecoverable")
    critical_r      = await _count_where(severity="CRITICAL")
    high_r          = await _count_where(severity="HIGH")
    medium_r        = await _count_where(severity="MEDIUM")
    low_r           = await _count_where(severity="LOW")

    return {
        "total_opportunities":     total or 0,
        "total_revenue_at_risk":   round(at_risk or 0, 2),
        "total_realized_revenue":  round(realized or 0, 2),
        "total_expected_revenue":  round(expected or 0, 2),
        "total_recoverable_amount": round(recoverable or 0, 2),
        "pending_count":       pending_r.scalar_one(),
        "in_progress_count":   in_progress_r.scalar_one(),
        "recovered_count":     recovered_r.scalar_one(),
        "unrecoverable_count": unrecoverable_r.scalar_one(),
        "critical_count": critical_r.scalar_one(),
        "high_count":     high_r.scalar_one(),
        "medium_count":   medium_r.scalar_one(),
        "low_count":      low_r.scalar_one(),
    }
