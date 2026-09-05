"""
RevTrace Phase 3 — Ingestion Tests.
Tests validation, normalization, duplicate skipping, and malformed row handling.
Uses SQLite in-memory so no live database is required.
"""
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Make sure backend root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.base import Base
import app.models.financial  # noqa: F401 — registers models with Base.metadata
from app.services.ingestion_service import (
    _flush_batch,
    _transaction_exists,
    get_database_stats,
)
from app.schemas.ingestion import RawPaymentRecord


# ── In-memory SQLite engine ───────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


# ── Sample valid record factory ───────────────────────────────────────────────

def make_record(**overrides) -> RawPaymentRecord:
    base = {
        "transaction_id": "txn_test_001",
        "customer_id":    "cust_11111",
        "merchant_id":    "merch_0001",
        "amount":         1500.00,
        "currency":       "INR",
        "payment_method": "upi",
        "timestamp":      "2023-06-01T10:00:00",
        "payment_status": "failed",
        "failure_reason": "timeout",
        "retry_count":    1,
        "previous_payment_history": "good",
        "recurring_payment": False,
        "refund_status":  "none",
        "recovery_status": "completed",
        "recovery_action": "automated_retry",
        "recovery_outcome": "success",
        "recovered_amount": 1500.00,
        "ground_truth_recoverable": True,
        "ground_truth_recovery_action": "automated_retry",
        "ground_truth_recovered_amount": 1500.00,
        "ground_truth_reason": "Timeouts usually recover on retry",
    }
    base.update(overrides)
    return RawPaymentRecord(**base)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_insert_single_record(session):
    """A valid record should be inserted successfully."""
    rec = make_record()
    ins, dup = await _flush_batch(session, [rec])
    await session.commit()
    assert ins == 1
    assert dup == 0
    assert await _transaction_exists(session, "txn_test_001")


@pytest.mark.asyncio
async def test_duplicate_skipped(session):
    """Inserting the same transaction_id twice should skip the second silently."""
    rec = make_record()
    ins1, dup1 = await _flush_batch(session, [rec])
    await session.flush()
    ins2, dup2 = await _flush_batch(session, [rec])
    await session.commit()

    assert ins1 == 1 and dup1 == 0
    assert ins2 == 0 and dup2 == 1


@pytest.mark.asyncio
async def test_malformed_amount_rejected():
    """A record with amount <= 0 should fail Pydantic validation."""
    with pytest.raises(Exception):
        make_record(amount=-100.0)


@pytest.mark.asyncio
async def test_recovered_amount_exceeds_amount_rejected():
    """recovered_amount > amount must be rejected at validation time."""
    with pytest.raises(Exception):
        make_record(amount=1000.0, recovered_amount=2000.0)


@pytest.mark.asyncio
async def test_success_with_recovered_amount_rejected():
    """Successful payments must not have recovered_amount > 0."""
    with pytest.raises(Exception):
        make_record(
            payment_status="success",
            failure_reason="",
            recovered_amount=500.0,
        )


@pytest.mark.asyncio
async def test_database_stats(session):
    """Stats endpoint should return correct row counts."""
    rec = make_record()
    await _flush_batch(session, [rec])
    await session.commit()
    stats = await get_database_stats(session)
    assert stats["customers"] == 1
    assert stats["merchants"] == 1
    assert stats["transactions"] == 1


@pytest.mark.asyncio
async def test_multiple_records_different_ids(session):
    """Multiple distinct transaction_ids should all be inserted."""
    records = [make_record(transaction_id=f"txn_test_{i:03d}") for i in range(5)]
    ins, dup = await _flush_batch(session, records)
    await session.commit()
    assert ins == 5
    assert dup == 0
    stats = await get_database_stats(session)
    assert stats["transactions"] == 5


@pytest.mark.asyncio
async def test_timestamp_normalised():
    """Timestamps without timezone should be made UTC-aware."""
    rec = make_record(timestamp="2023-01-15T08:30:00")
    ts = rec.normalized_timestamp()
    import datetime
    assert ts.tzinfo == datetime.timezone.utc


@pytest.mark.asyncio
async def test_invalid_payment_status_rejected():
    """An unknown payment_status value must fail validation."""
    with pytest.raises(Exception):
        make_record(payment_status="mystery_status")
