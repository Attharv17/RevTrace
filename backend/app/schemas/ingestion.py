"""
RevTrace — Pydantic ingestion schemas.
Validates and normalizes raw CSV rows before database insertion.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


# ── Allowed enumerations ─────────────────────────────────────────────────────

VALID_PAYMENT_STATUSES = {"success", "failed", "pending"}
VALID_PAYMENT_METHODS = {"upi", "card", "netbanking", "wallet"}
VALID_CURRENCIES = {"INR"}
VALID_REFUND_STATUSES = {"none", "partial", "full"}
VALID_RECOVERY_STATUSES = {"not_applicable", "pending", "in_progress", "completed", "failed"}
VALID_RECOVERY_OUTCOMES = {"not_applicable", "success", "partial", "failure", "pending"}
VALID_HISTORY = {"good", "average", "poor"}


# ── Raw CSV Row schema ────────────────────────────────────────────────────────

class RawPaymentRecord(BaseModel):
    """Validates and normalises one row from the synthetic payment CSV."""

    model_config = {"str_strip_whitespace": True}

    # Identifiers
    transaction_id: str
    customer_id: str
    merchant_id: str

    # Financial
    amount: float
    currency: str
    payment_method: str

    # Temporal
    timestamp: str  # raw string; normalised in validator

    # Status
    payment_status: str
    failure_reason: Optional[str] = None
    retry_count: int = 0
    previous_payment_history: Optional[str] = None
    recurring_payment: bool = False
    refund_status: str = "none"

    # Recovery
    recovery_status: str = "not_applicable"
    recovery_action: str = "none"
    recovery_outcome: str = "not_applicable"
    recovered_amount: float = 0.0

    # Ground truth labels
    ground_truth_recoverable: bool = False
    ground_truth_recovery_action: str = "none"
    ground_truth_recovered_amount: float = 0.0
    ground_truth_reason: str = ""

    # ── Field validators ──────────────────────────────────────────────────────

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        val = float(v)
        if val <= 0:
            raise ValueError(f"amount must be > 0, got {val}")
        return round(val, 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Unsupported currency: {v!r}")
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Unknown payment_method: {v!r}")
        return v

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_PAYMENT_STATUSES:
            raise ValueError(f"Unknown payment_status: {v!r}")
        return v

    @field_validator("refund_status")
    @classmethod
    def validate_refund_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_REFUND_STATUSES:
            raise ValueError(f"Unknown refund_status: {v!r}")
        return v

    @field_validator("retry_count", mode="before")
    @classmethod
    def validate_retry_count(cls, v) -> int:
        val = int(v)
        if val < 0:
            raise ValueError("retry_count cannot be negative")
        return val

    @field_validator("recovered_amount", "ground_truth_recovered_amount", mode="before")
    @classmethod
    def validate_recovered_amount(cls, v) -> float:
        val = float(v)
        if val < 0:
            raise ValueError("Recovered amounts cannot be negative")
        return round(val, 2)

    @field_validator("recurring_payment", mode="before")
    @classmethod
    def parse_bool(cls, v) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"true", "1", "yes"}
        return bool(v)

    @field_validator("ground_truth_recoverable", mode="before")
    @classmethod
    def parse_gt_bool(cls, v) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"true", "1", "yes"}
        return bool(v)

    # ── Cross-field validation ────────────────────────────────────────────────

    @model_validator(mode="after")
    def validate_financial_consistency(self) -> "RawPaymentRecord":
        if self.recovered_amount > self.amount:
            raise ValueError(
                f"recovered_amount ({self.recovered_amount}) "
                f"cannot exceed amount ({self.amount})"
            )
        if self.ground_truth_recovered_amount > self.amount:
            raise ValueError(
                f"ground_truth_recovered_amount ({self.ground_truth_recovered_amount}) "
                f"cannot exceed amount ({self.amount})"
            )
        if self.payment_status == "success" and self.recovered_amount > 0:
            raise ValueError(
                "Successful payments should not have recovered_amount > 0"
            )
        return self

    # ── Normalisation helpers ─────────────────────────────────────────────────

    def normalized_timestamp(self) -> datetime:
        """Parse and normalise the raw ISO timestamp to UTC-aware datetime."""
        ts = datetime.fromisoformat(self.timestamp)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    def normalized_failure_reason(self) -> Optional[str]:
        if not self.failure_reason:
            return None
        return self.failure_reason.lower().strip() or None


# ── Response schemas ──────────────────────────────────────────────────────────

class IngestionStats(BaseModel):
    """Summary returned after a batch ingestion run."""
    total_rows_read: int
    inserted: int
    duplicates_skipped: int
    malformed_skipped: int
    duration_seconds: float


class DatabaseStats(BaseModel):
    """Row counts per table — returned by GET /api/ingestion/stats."""
    customers: int
    merchants: int
    transactions: int
    payment_attempts: int
