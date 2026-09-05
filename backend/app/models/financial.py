from datetime import datetime
from typing import Optional, Union
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"))

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment_status: Mapped[str] = mapped_column(String, nullable=False)
    # Use column() with nullable=True to avoid Optional[str] Mapped annotation on Py3.14
    failure_reason = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    previous_payment_history = mapped_column(String, nullable=True)
    recurring_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_status: Mapped[str] = mapped_column(String, default="none")

    # Ground truth — stored for AI evaluation in Phase 4+
    ground_truth_recoverable: Mapped[bool] = mapped_column(Boolean, default=False)
    ground_truth_recovery_action: Mapped[str] = mapped_column(String, nullable=True)
    ground_truth_recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)
    ground_truth_reason = mapped_column(String, nullable=True)

    customer = relationship("Customer")
    merchant = relationship("Merchant")
    payment_attempts = relationship(
        "PaymentAttempt", back_populates="transaction", cascade="all, delete-orphan"
    )


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"))
    recovery_action: Mapped[str] = mapped_column(String, nullable=False)
    recovery_outcome: Mapped[str] = mapped_column(String, nullable=False)
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transaction = relationship("Transaction", back_populates="payment_attempts")
