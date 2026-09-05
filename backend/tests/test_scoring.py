"""
RevTrace Phase 5 — Recovery Scoring Engine Tests.
"""
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.base import Base
import app.models.financial   # noqa
import app.models.opportunity  # noqa

from app.services.scoring_engine import (
    calculate_base_probability,
    determine_band_and_action,
    run_scoring,
)
from app.services.ingestion_service import _flush_batch
from app.services.leakage_engine import detect_leakage
from app.schemas.ingestion import RawPaymentRecord


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    AsyncSession_ = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSession_() as s:
        yield s
    await engine.dispose()


def make_record(**overrides) -> RawPaymentRecord:
    base = {
        "transaction_id": "txn_test_001",
        "customer_id":    "cust_11111",
        "merchant_id":    "merch_0001",
        "amount":         5000.00,
        "currency":       "INR",
        "payment_method": "upi",
        "timestamp":      "2023-06-01T10:00:00",
        "payment_status": "failed",
        "failure_reason": "timeout",
        "retry_count":    0,
        "previous_payment_history": "good",
        "recurring_payment": False,
        "refund_status":  "none",
        "recovery_status": "not_applicable",
        "recovery_action": "none",
        "recovery_outcome": "not_applicable",
        "recovered_amount": 0.0,
        "ground_truth_recoverable": True,
        "ground_truth_recovery_action": "automated_retry",
        "ground_truth_recovered_amount": 5000.00,
        "ground_truth_reason": "Timeouts usually recover on retry",
    }
    base.update(overrides)
    if "amount" in overrides and "ground_truth_recovered_amount" not in overrides:
        base["ground_truth_recovered_amount"] = overrides["amount"]
    return RawPaymentRecord(**base)


# ── Pure Function Tests ──────────────────────────────────────────────────────

class TestScoringCalculations:
    def test_base_probability_timeout_good_history(self):
        # 0.5 (base) + 0.3 (timeout) + 0.2 (good history) = 1.0
        prob = calculate_base_probability("timeout", "good", 0)
        assert prob == 1.0

    def test_base_probability_insufficient_funds_poor_history(self):
        # 0.5 (base) + 0.1 (insufficient_funds) - 0.2 (poor history) = 0.4
        prob = calculate_base_probability("insufficient_funds", "poor", 0)
        assert prob == 0.4

    def test_base_probability_hard_decline(self):
        # 0.5 (base) - 0.5 (card_blocked_or_stolen) = 0.0 (clamped)
        prob = calculate_base_probability("card_blocked_or_stolen", "poor", 0)
        assert prob == 0.0
        
    def test_retry_penalty(self):
        # 0.5 (base) + 0.3 (timeout) + 0.2 (good history) - (0.05 * 2) = 0.9
        prob = calculate_base_probability("timeout", "good", 2)
        assert prob == 0.9

    def test_determine_band_green(self):
        band, priority, action = determine_band_and_action(0.8, 15000.0)
        assert band == "GREEN"
        assert priority == "HIGH"
        assert "Retry" in action

    def test_determine_band_amber(self):
        band, priority, action = determine_band_and_action(0.5, 5000.0)
        assert band == "AMBER"
        assert priority == "MEDIUM"
        assert "Manual" in action

    def test_determine_band_red(self):
        band, priority, action = determine_band_and_action(0.2, 5000.0)
        assert band == "RED"
        assert priority == "LOW"
        assert "No Action" in action


# ── Integration Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_scoring_engine(session):
    # Setup data
    records = [
        make_record(transaction_id="txn_1", failure_reason="timeout", previous_payment_history="good", amount=5000.0),
        make_record(transaction_id="txn_2", failure_reason="insufficient_funds", previous_payment_history="poor", amount=3000.0),
        make_record(transaction_id="txn_3", failure_reason="card_blocked_or_stolen", previous_payment_history="good", amount=8000.0),
    ]
    await _flush_batch(session, records)
    await session.commit()

    # Detect leakage first
    await detect_leakage(session)
    
    # Run scoring
    stats = await run_scoring(session)
    
    assert stats.opportunities_scanned == 3
    assert stats.opportunities_scored == 3
    
    # Verify DB records
    from app.models.opportunity import RecoveryOpportunity
    result = await session.execute(select(RecoveryOpportunity).order_by(RecoveryOpportunity.transaction_id))
    opps = result.scalars().all()
    
    assert len(opps) == 3
    
    # txn_1: timeout (0.3) + good (0.2) = 1.0 (GREEN)
    assert opps[0].recovery_probability == 1.0
    assert opps[0].expected_recovery == 5000.0
    assert opps[0].decision_band == "GREEN"
    assert opps[0].priority == "MEDIUM"  # Since amount is 5000 <= 10000
    
    # txn_2: insufficient_funds (0.1) + poor (-0.2) = 0.4 (AMBER)
    assert opps[1].recovery_probability == 0.4
    assert opps[1].expected_recovery == 1200.0
    assert opps[1].decision_band == "AMBER"
    
    # txn_3: hard decline overrides to 0.0 (RED)
    assert opps[2].recovery_probability == 0.0
    assert opps[2].expected_recovery == 0.0
    assert opps[2].decision_band == "RED"
    assert opps[2].priority == "LOW"
    
    assert opps[0].score_version == "1.0.0-deterministic"
    assert opps[0].score_metadata is not None
    assert opps[0].scored_at is not None
