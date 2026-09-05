"""
RevTrace Phase 4 — Revenue Leakage Detection Tests.

Tests the deterministic calculation functions directly (no DB needed for pure logic),
plus integration tests against in-memory SQLite for the full detect_leakage flow.
"""
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.base import Base
import app.models.financial   # noqa
import app.models.opportunity  # noqa

from app.services.leakage_engine import (
    compute_realized_revenue,
    compute_revenue_at_risk,
    compute_severity,
    compute_status,
    detect_leakage,
)
from app.services.ingestion_service import _flush_batch
from app.schemas.ingestion import RawPaymentRecord


# ── Shared in-memory SQLite fixture ──────────────────────────────────────────

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


# ── Record helpers ────────────────────────────────────────────────────────────

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
        "retry_count":    1,
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
    return RawPaymentRecord(**base)


# ═══════════════════════════════════════════════════════════════════════════
# PURE FUNCTION TESTS (no database required)
# ═══════════════════════════════════════════════════════════════════════════

class TestComputeRealizedRevenue:
    def test_no_attempts_returns_zero(self):
        assert compute_realized_revenue([]) == 0.0

    def test_successful_attempt_counts(self):
        assert compute_realized_revenue([("success", 5000.0)]) == 5000.0

    def test_partial_attempt_counts(self):
        assert compute_realized_revenue([("partial", 2000.0)]) == 2000.0

    def test_failed_attempt_does_not_count(self):
        assert compute_realized_revenue([("failure", 5000.0)]) == 0.0

    def test_pending_attempt_does_not_count(self):
        assert compute_realized_revenue([("pending", 5000.0)]) == 0.0

    def test_multiple_attempts_sums_only_successful(self):
        attempts = [
            ("failure", 5000.0),
            ("partial", 2000.0),
            ("success", 1000.0),
        ]
        assert compute_realized_revenue(attempts) == 3000.0


class TestComputeRevenueAtRisk:
    def test_no_recovery_full_amount_at_risk(self):
        assert compute_revenue_at_risk(5000.0, 0.0) == 5000.0

    def test_partial_recovery_reduces_risk(self):
        assert compute_revenue_at_risk(5000.0, 2000.0) == 3000.0

    def test_full_recovery_zero_risk(self):
        assert compute_revenue_at_risk(5000.0, 5000.0) == 0.0

    def test_never_negative_even_if_recovered_exceeds_expected(self):
        # Should not happen in practice, but rule must hold
        assert compute_revenue_at_risk(5000.0, 6000.0) == 0.0

    def test_zero_amount_zero_risk(self):
        assert compute_revenue_at_risk(0.0, 0.0) == 0.0


class TestComputeSeverity:
    def test_critical_above_25000(self):
        assert compute_severity(25001.0) == "CRITICAL"

    def test_high_above_10000(self):
        assert compute_severity(15000.0) == "HIGH"

    def test_medium_above_2500(self):
        assert compute_severity(5000.0) == "MEDIUM"

    def test_low_at_or_below_2500(self):
        assert compute_severity(2500.0) == "LOW"
        assert compute_severity(100.0) == "LOW"
        assert compute_severity(0.0) == "LOW"


class TestComputeStatus:
    def test_unrecoverable_when_ground_truth_says_so(self):
        assert compute_status(False, []) == "unrecoverable"

    def test_unrecoverable_overrides_successful_attempts(self):
        # Ground truth says unrecoverable regardless of attempts
        assert compute_status(False, [("success", 5000.0)]) == "unrecoverable"

    def test_recovered_when_successful_attempt_exists(self):
        assert compute_status(True, [("success", 5000.0)]) == "recovered"

    def test_in_progress_when_pending_attempt_exists(self):
        assert compute_status(True, [("pending", 0.0)]) == "in_progress"

    def test_pending_when_no_attempts_and_recoverable(self):
        assert compute_status(True, []) == "pending"

    def test_pending_when_only_failed_attempts_and_recoverable(self):
        assert compute_status(True, [("failure", 0.0)]) == "pending"


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS (uses in-memory SQLite via fixture)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_successful_payment_produces_no_opportunity(session):
    """A successful payment has no leakage — no opportunity should be created."""
    rec = make_record(
        payment_status="success",
        failure_reason="",
        recovered_amount=0.0,
        ground_truth_recoverable=False,
        ground_truth_recovered_amount=0.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    stats = await detect_leakage(session)
    assert stats.opportunities_created == 0
    assert stats.skipped_not_applicable == 1


@pytest.mark.asyncio
async def test_failed_5000_no_recovery_full_risk(session):
    """Failed Rs 5,000 transaction with no recovery → revenue_at_risk = 5,000."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select

    rec = make_record(
        transaction_id="txn_t5k",
        amount=5000.0,
        payment_status="failed",
        failure_reason="timeout",
        recovery_action="none",
        recovery_outcome="not_applicable",
        recovered_amount=0.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)

    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_t5k"
        )
    )
    opp = result.scalar_one()

    assert opp.expected_revenue == 5000.0
    assert opp.realized_revenue == 0.0
    assert opp.revenue_at_risk == 5000.0


@pytest.mark.asyncio
async def test_partial_collection_correct_difference(session):
    """Failed Rs 5,000 with Rs 2,000 recovered → revenue_at_risk = 3,000."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select

    rec = make_record(
        transaction_id="txn_partial",
        amount=5000.0,
        payment_status="failed",
        failure_reason="insufficient_funds",
        recovery_action="payment_link_sms",
        recovery_outcome="partial",
        recovered_amount=2000.0,
        ground_truth_recoverable=True,
        ground_truth_recovered_amount=2000.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)

    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_partial"
        )
    )
    opp = result.scalar_one()

    assert opp.expected_revenue == 5000.0
    assert opp.realized_revenue == 2000.0
    assert opp.revenue_at_risk == 3000.0
    # 'partial' outcome does not qualify as 'success' in compute_status —
    # status is 'pending' because no attempt has outcome == 'success'
    assert opp.status == "pending"


@pytest.mark.asyncio
async def test_full_recovery_zero_risk_and_recovered_status(session):
    """Full recovery → revenue_at_risk = 0, status = recovered."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select

    rec = make_record(
        transaction_id="txn_full_rec",
        amount=5000.0,
        payment_status="failed",
        failure_reason="timeout",
        recovery_action="automated_retry",
        recovery_outcome="success",
        recovered_amount=5000.0,
        ground_truth_recoverable=True,
        ground_truth_recovered_amount=5000.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)

    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_full_rec"
        )
    )
    opp = result.scalar_one()

    assert opp.realized_revenue == 5000.0
    assert opp.revenue_at_risk == 0.0
    assert opp.status == "recovered"


@pytest.mark.asyncio
async def test_revenue_at_risk_never_negative(session):
    """revenue_at_risk must never be negative, even in edge cases."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select

    # This scenario is impossible in valid data but the engine must still hold
    rec = make_record(
        transaction_id="txn_edge",
        amount=1000.0,
        payment_status="failed",
        failure_reason="user_abandoned",
        recovery_action="payment_link_email",
        recovery_outcome="success",
        recovered_amount=1000.0,
        ground_truth_recoverable=True,
        ground_truth_recovered_amount=1000.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)

    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_edge"
        )
    )
    opp = result.scalar_one()
    assert opp.revenue_at_risk >= 0.0


@pytest.mark.asyncio
async def test_unrecoverable_transaction_status(session):
    """Hard decline → status = unrecoverable."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select

    rec = make_record(
        transaction_id="txn_hard",
        amount=8000.0,
        payment_status="failed",
        failure_reason="card_blocked_or_stolen",
        recovery_action="none",
        recovery_outcome="not_applicable",
        recovered_amount=0.0,
        ground_truth_recoverable=False,
        ground_truth_recovered_amount=0.0,
        ground_truth_reason="Hard declines are unrecoverable",
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)

    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_hard"
        )
    )
    opp = result.scalar_one()
    assert opp.status == "unrecoverable"
    assert opp.revenue_at_risk == 8000.0


@pytest.mark.asyncio
async def test_detection_is_idempotent(session):
    """Running detect_leakage twice must not duplicate opportunities."""
    from app.models.opportunity import RecoveryOpportunity
    from sqlalchemy import select, func

    rec = make_record(
        transaction_id="txn_idem",
        amount=3000.0,
        ground_truth_recovered_amount=3000.0,
    )
    await _flush_batch(session, [rec])
    await session.commit()

    await detect_leakage(session)
    await detect_leakage(session)

    result = await session.execute(
        select(func.count()).select_from(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == "txn_idem"
        )
    )
    assert result.scalar_one() == 1
