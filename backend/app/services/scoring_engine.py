"""
RevTrace — Recovery Scoring Engine (Phase 5).

Deterministic baseline for scoring recovery opportunities.
Calculates recovery probability and expected recovery based on 
failure reason, payment history, and amount.
Assigns decision bands (GREEN, AMBER, RED) without ML or LLMs.
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Transaction
from app.models.opportunity import RecoveryOpportunity
from app.schemas.opportunity import ScoringRunStats

logger = logging.getLogger(__name__)

SCORE_VERSION = "1.0.0-deterministic"


# ── Scoring Helpers ─────────────────────────────────────────────────────────

def calculate_base_probability(
    failure_reason: str,
    payment_history: str,
    retry_count: int
) -> float:
    """Calculate the base recovery probability (0.0 to 1.0)."""
    score = 0.5  # Base score
    
    # Reason adjustments
    reason_lower = (failure_reason or "").lower()
    if reason_lower in ["timeout", "link_expired", "user_abandoned"]:
        score += 0.3  # High intent, easily recoverable
    elif reason_lower in ["insufficient_funds", "mandate_failed"]:
        score += 0.1
    elif reason_lower == "card_blocked_or_stolen":
        score -= 0.5  # Hard decline, typically unrecoverable
        
    # History adjustments
    history_lower = (payment_history or "").lower()
    if history_lower == "good":
        score += 0.2
    elif history_lower == "poor":
        score -= 0.2
        
    # Retry penalty (diminishing returns)
    if retry_count > 0:
        score -= (0.05 * retry_count)
        
    return round(max(0.0, min(1.0, score)), 4)


def determine_band_and_action(
    probability: float,
    revenue_at_risk: float
) -> Tuple[str, str, str]:
    """
    Returns (decision_band, priority, recommended_action).
    """
    if probability < 0.4:
        band = "RED"
        priority = "LOW"
        action = "No Action / Unrecoverable"
    elif probability >= 0.7:
        band = "GREEN"
        priority = "HIGH" if revenue_at_risk > 10000 else "MEDIUM"
        action = "Automated Retry / Direct Link"
    else:
        band = "AMBER"
        priority = "MEDIUM" if revenue_at_risk > 2500 else "LOW"
        action = "Manual Review / SMS Nudge"
        
    return band, priority, action


# ── Core Engine ─────────────────────────────────────────────────────────────

async def run_scoring(session: AsyncSession) -> ScoringRunStats:
    """
    Score all pending and in_progress opportunities that lack a current score.
    """
    t_start = time.perf_counter()
    scanned = 0
    scored = 0
    
    # Get all unscored or outdated opportunities (for now, just score all that aren't fully recovered/unrecoverable)
    # To be idempotent, we can re-score everything that isn't in terminal status, or just score all.
    # Let's score all opportunities that are not in terminal status (recovered, unrecoverable)
    # OR we can just score all opportunities. The prompt says "Store: score, score version...".
    
    # Let's just query all opportunities and their joined transaction
    result = await session.execute(
        select(RecoveryOpportunity, Transaction)
        .join(Transaction, RecoveryOpportunity.transaction_id == Transaction.transaction_id)
    )
    
    rows = result.all()
    
    for opp, txn in rows:
        scanned += 1
        
        # Calculate new score
        probability = calculate_base_probability(
            failure_reason=txn.failure_reason,
            payment_history=txn.previous_payment_history,
            retry_count=txn.retry_count or 0
        )
        
        band, priority, action = determine_band_and_action(probability, opp.revenue_at_risk)
        
        expected_recovery = round(opp.revenue_at_risk * probability, 2)
        
        # We override for hard declines to ensure they are RED.
        if txn.failure_reason == "card_blocked_or_stolen":
            probability = 0.0
            expected_recovery = 0.0
            band = "RED"
            priority = "LOW"
            action = "No Action (Hard Decline)"
            
        metadata = {
            "failure_reason": txn.failure_reason,
            "payment_history": txn.previous_payment_history,
            "retry_count": txn.retry_count,
            "revenue_at_risk": opp.revenue_at_risk,
        }
        
        # Update the opportunity
        opp.recovery_probability = round(probability, 4)
        opp.expected_recovery = expected_recovery
        opp.decision_band = band
        opp.priority = priority
        opp.recommended_action = action
        opp.score_version = SCORE_VERSION
        opp.score_metadata = json.dumps(metadata)
        opp.scored_at = datetime.now(timezone.utc)
        
        scored += 1
        
    await session.commit()
    duration = round(time.perf_counter() - t_start, 3)
    
    logger.info("Scoring complete: scanned %d, scored %d in %.2fs", scanned, scored, duration)
    
    return ScoringRunStats(
        opportunities_scanned=scanned,
        opportunities_scored=scored,
        duration_seconds=duration
    )
