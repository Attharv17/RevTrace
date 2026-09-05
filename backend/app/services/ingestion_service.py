"""
RevTrace — Ingestion Service (Phase 3).
Reads CSV rows → validates via Pydantic → normalises → batch-upserts into PostgreSQL/SQLite.
Transactions are treated as immutable source records; duplicates are silently skipped.
"""
from __future__ import annotations

import csv
import logging
import time
from pathlib import Path
from typing import List, Tuple

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.financial import Customer, Merchant, PaymentAttempt, Transaction
from app.schemas.ingestion import DatabaseStats, IngestionStats, RawPaymentRecord

logger = logging.getLogger(__name__)

# Detect dialect once at import time from the engine URL string
_IS_POSTGRES = "postgresql" in str(engine.url)


# ── Dialect-aware upsert ──────────────────────────────────────────────────────

async def _upsert_ignore(session: AsyncSession, model, values: dict) -> None:
    """Insert a row, silently skipping if the primary key already exists."""
    if _IS_POSTGRES:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        stmt = pg_insert(model).values(**values).on_conflict_do_nothing()
    else:
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        stmt = sqlite_insert(model).values(**values).prefix_with("OR IGNORE")
    await session.execute(stmt)


# ── Stats ─────────────────────────────────────────────────────────────────────

async def _count_table(session: AsyncSession, model) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return result.scalar_one()


async def get_database_stats(session: AsyncSession) -> dict:
    return {
        "customers": await _count_table(session, Customer),
        "merchants": await _count_table(session, Merchant),
        "transactions": await _count_table(session, Transaction),
        "payment_attempts": await _count_table(session, PaymentAttempt),
    }


# ── Existence check (for duplicate detection) ─────────────────────────────────

async def _transaction_exists(session: AsyncSession, transaction_id: str) -> bool:
    result = await session.execute(
        select(Transaction.transaction_id).where(
            Transaction.transaction_id == transaction_id
        )
    )
    return result.first() is not None


# ── Batch flush ───────────────────────────────────────────────────────────────

async def _flush_batch(
    session: AsyncSession,
    records: List[RawPaymentRecord],
) -> Tuple[int, int]:
    """
    Upsert a batch of validated records.
    Returns (inserted_count, duplicate_count).
    """
    inserted = 0
    duplicates = 0

    for rec in records:
        await _upsert_ignore(session, Customer, {"id": rec.customer_id})
        await _upsert_ignore(session, Merchant, {"id": rec.merchant_id})

        if await _transaction_exists(session, rec.transaction_id):
            duplicates += 1
            continue

        txn_values = {
            "transaction_id": rec.transaction_id,
            "customer_id":    rec.customer_id,
            "merchant_id":    rec.merchant_id,
            "amount":         rec.amount,
            "currency":       rec.currency,
            "payment_method": rec.payment_method,
            "timestamp":      rec.normalized_timestamp(),
            "payment_status": rec.payment_status,
            "failure_reason": rec.normalized_failure_reason(),
            "retry_count":    rec.retry_count,
            "previous_payment_history": rec.previous_payment_history,
            "recurring_payment":        rec.recurring_payment,
            "refund_status":            rec.refund_status,
            "ground_truth_recoverable":       rec.ground_truth_recoverable,
            "ground_truth_recovery_action":   rec.ground_truth_recovery_action,
            "ground_truth_recovered_amount":  rec.ground_truth_recovered_amount,
            "ground_truth_reason":            rec.ground_truth_reason,
        }
        await _upsert_ignore(session, Transaction, txn_values)
        inserted += 1

        # Insert a PaymentAttempt row only when recovery was actually attempted
        if (
            rec.recovery_action not in ("none", "")
            and rec.recovery_outcome not in ("not_applicable", "")
        ):
            await _upsert_ignore(
                session,
                PaymentAttempt,
                {
                    "transaction_id":  rec.transaction_id,
                    "recovery_action": rec.recovery_action,
                    "recovery_outcome": rec.recovery_outcome,
                    "recovered_amount": rec.recovered_amount,
                },
            )

    return inserted, duplicates


# ── Core pipeline ─────────────────────────────────────────────────────────────

async def ingest_csv_batch(
    csv_path: str,
    session: AsyncSession,
    chunk_size: int = 100,
) -> IngestionStats:
    """
    Read a CSV of payment records, validate/normalise, and insert into the DB.
    Idempotent — safe to call multiple times on the same file.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    t_start = time.perf_counter()
    total_rows_read = 0
    inserted = 0
    duplicates_skipped = 0
    malformed_skipped = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch: List[RawPaymentRecord] = []

        for row in reader:
            total_rows_read += 1
            try:
                record = RawPaymentRecord(**row)
                batch.append(record)
            except (ValidationError, ValueError, Exception) as exc:
                malformed_skipped += 1
                logger.warning("Row %d malformed — skipped: %s", total_rows_read, exc)
                continue

            if len(batch) >= chunk_size:
                ins, dup = await _flush_batch(session, batch)
                inserted += ins
                duplicates_skipped += dup
                batch = []
                await session.flush()

        if batch:
            ins, dup = await _flush_batch(session, batch)
            inserted += ins
            duplicates_skipped += dup

    await session.commit()
    duration = round(time.perf_counter() - t_start, 3)

    logger.info(
        "Ingestion complete: %d read, %d inserted, %d duplicates, %d malformed in %.2fs",
        total_rows_read, inserted, duplicates_skipped, malformed_skipped, duration,
    )

    return IngestionStats(
        total_rows_read=total_rows_read,
        inserted=inserted,
        duplicates_skipped=duplicates_skipped,
        malformed_skipped=malformed_skipped,
        duration_seconds=duration,
    )
