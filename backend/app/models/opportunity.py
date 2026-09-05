"""
RevTrace — RecoveryOpportunity database model (Phase 4).
One row per failed transaction. Treated as a derived, computed record —
source financial values always trace back to the immutable transactions table.
"""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # One opportunity per transaction — enforced at DB level
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("transactions.transaction_id"), unique=True, nullable=False
    )

    # ── Verified financial figures (all derived from source transaction) ──────
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    realized_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_at_risk: Mapped[float] = mapped_column(Float, nullable=False)

    # Ground truth recoverable amount (labelled as ground truth, not a live prediction)
    recoverable_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Classification ────────────────────────────────────────────────────────
    reason: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)   # LOW/MEDIUM/HIGH/CRITICAL
    status: Mapped[str] = mapped_column(String, nullable=False)     # pending/in_progress/recovered/unrecoverable

    # ── Phase 5: Scoring ──────────────────────────────────────────────────────
    recovery_probability: Mapped[float] = mapped_column(Float, nullable=True)
    expected_recovery: Mapped[float] = mapped_column(Float, nullable=True)
    priority: Mapped[str] = mapped_column(String, nullable=True)
    recommended_action: Mapped[str] = mapped_column(String, nullable=True)
    decision_band: Mapped[str] = mapped_column(String, nullable=True) # GREEN, AMBER, RED
    score_version: Mapped[str] = mapped_column(String, nullable=True)
    score_metadata: Mapped[str] = mapped_column(String, nullable=True) # JSON stored as string for simplicity across dialects
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship back to source transaction
    transaction = relationship("Transaction")

    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_opportunity_transaction"),
    )
