"""
RevTrace — Phase 7: AI Investigation Agent Tests.

Test strategy:
  1. Tool function unit tests (no DB, no LLM) — pure logic
  2. Tool integration tests against in-memory SQLite
  3. Degraded report tests (LLM unavailable path)
  4. Hallucination-resistance: missing/invalid transaction IDs
  5. Report schema validation — all required fields present

The LLM itself is NOT tested here (would require a live API key).
These tests verify that the data retrieval layer is correct and
that the agent never invents data when a transaction is not found.
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.base import Base
import app.models.financial   # noqa — registers ORM tables
import app.models.opportunity  # noqa

from app.services.investigation_agent import (
    _tool_get_transaction,
    _tool_get_customer_history,
    _tool_get_payment_attempts,
    _tool_get_recovery_history,
    _tool_get_opportunity,
    _tool_get_verified_metrics,
    _build_degraded_report,
    _parse_llm_json,
    _summarize_result,
)
from app.services.ingestion_service import _flush_batch
from app.services.leakage_engine import detect_leakage
from app.services.scoring_engine import run_scoring
from app.schemas.ingestion import RawPaymentRecord
from app.schemas.investigation import InvestigationReport


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ── Shared in-memory SQLite fixture ──────────────────────────────────────────

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
        "transaction_id": "TXN10291",
        "customer_id":    "CUST_AAA",
        "merchant_id":    "MERCH_001",
        "amount":         15000.00,
        "currency":       "INR",
        "payment_method": "upi",
        "timestamp":      "2024-01-15T10:30:00",
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
        "ground_truth_recovered_amount": 15000.00,
        "ground_truth_reason": "Timeouts usually recover on retry",
    }
    base.update(overrides)
    return RawPaymentRecord(**base)


# ═══════════════════════════════════════════════════════════════════════════
# TOOL UNIT TESTS — Pure function tests (no DB)
# ═══════════════════════════════════════════════════════════════════════════

class TestParseLlmJson:
    """Test the JSON parser for LLM responses."""

    def test_valid_json_parsed(self):
        text = '{"evidence": ["A", "B"], "revenue_impact": "₹5k", "recommendation": "retry", "confidence_note": "high"}'
        result = _parse_llm_json(text)
        assert result["evidence"] == ["A", "B"]
        assert result["revenue_impact"] == "₹5k"

    def test_markdown_fenced_json_stripped(self):
        text = '```json\n{"evidence": ["X"], "revenue_impact": "Y"}\n```'
        result = _parse_llm_json(text)
        assert result["evidence"] == ["X"]

    def test_invalid_json_returns_fallback(self):
        result = _parse_llm_json("not json at all")
        assert "evidence" in result
        assert isinstance(result["evidence"], list)

    def test_empty_string_returns_empty(self):
        result = _parse_llm_json("")
        assert result == {}

    def test_evidence_coerced_to_list(self):
        # If LLM returns evidence as a string, should be wrapped in list
        result = _parse_llm_json('{"evidence": "just a string"}')
        assert isinstance(result["evidence"], list)


class TestSummarizeResult:
    """Test the audit log summary generator."""

    def test_transaction_found_summary(self):
        result = {"found": True, "amount": 5000, "currency": "INR", "payment_status": "failed"}
        summary = _summarize_result("get_transaction", result)
        assert "5,000" in summary or "5000" in summary

    def test_opportunity_found_summary(self):
        result = {
            "found": True, "revenue_at_risk": 10000,
            "decision_band": "GREEN", "recovery_probability": 0.75
        }
        summary = _summarize_result("get_opportunity", result)
        assert "GREEN" in summary

    def test_payment_attempts_summary(self):
        result = {"total_attempts": 3, "attempts": []}
        summary = _summarize_result("get_payment_attempts", result)
        assert "3" in summary


# ═══════════════════════════════════════════════════════════════════════════
# TOOL INTEGRATION TESTS — Against in-memory SQLite
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_transaction_found(session):
    """get_transaction returns correct data for a known transaction."""
    await _flush_batch(session, [make_record()])
    await session.commit()

    result = await _tool_get_transaction(session, "TXN10291")
    assert result["found"] is True
    assert result["transaction_id"] == "TXN10291"
    assert result["amount"] == 15000.00
    assert result["currency"] == "INR"
    assert result["payment_status"] == "failed"
    assert result["failure_reason"] == "timeout"


@pytest.mark.asyncio
async def test_get_transaction_not_found_returns_found_false(session):
    """
    HALLUCINATION TEST: get_transaction with an invalid ID must return found=False.
    The tool MUST NOT invent a transaction or return any fabricated data.
    """
    result = await _tool_get_transaction(session, "TXN_DOES_NOT_EXIST_99999")
    assert result["found"] is False
    assert result["transaction_id"] == "TXN_DOES_NOT_EXIST_99999"
    # Critically: no financial data should be in the result
    assert "amount" not in result
    assert "customer_id" not in result


@pytest.mark.asyncio
async def test_get_transaction_empty_id_not_found(session):
    """Empty string ID must return not-found, not crash."""
    result = await _tool_get_transaction(session, "")
    assert result["found"] is False


@pytest.mark.asyncio
async def test_get_customer_history_found(session):
    """get_customer_history returns aggregated stats for known customer."""
    await _flush_batch(session, [make_record()])
    await session.commit()

    result = await _tool_get_customer_history(session, "TXN10291")
    assert result["found"] is True
    assert result["customer_id"] == "CUST_AAA"
    assert result["total_transactions"] == 1
    assert result["failed_transactions"] == 1
    assert "upi" in result["payment_methods_used"]


@pytest.mark.asyncio
async def test_get_customer_history_invalid_txn_returns_not_found(session):
    """
    HALLUCINATION TEST: get_customer_history with invalid txn_id must NOT
    fabricate customer data.
    """
    result = await _tool_get_customer_history(session, "TXN_INVALID_HALLUCINATION_TEST")
    assert result["found"] is False
    assert "total_transactions" not in result


@pytest.mark.asyncio
async def test_get_payment_attempts_none_for_new_transaction(session):
    """New transaction has zero payment attempts."""
    await _flush_batch(session, [make_record()])
    await session.commit()

    result = await _tool_get_payment_attempts(session, "TXN10291")
    assert result["total_attempts"] == 0
    assert result["attempts"] == []


@pytest.mark.asyncio
async def test_get_payment_attempts_invalid_txn_returns_empty_not_fabricated(session):
    """
    HALLUCINATION TEST: invalid transaction ID should return 0 attempts, not fabricated history.
    """
    result = await _tool_get_payment_attempts(session, "INVALID_TXN_XYZ")
    assert result["total_attempts"] == 0
    assert result["attempts"] == []


@pytest.mark.asyncio
async def test_get_recovery_history_found(session):
    """get_recovery_history returns correct ground truth data."""
    await _flush_batch(session, [make_record()])
    await session.commit()

    result = await _tool_get_recovery_history(session, "TXN10291")
    assert result["found"] is True
    assert result["ground_truth_recoverable"] is True
    assert result["ground_truth_recovery_action"] == "automated_retry"
    assert result["ground_truth_recovered_amount"] == 15000.00


@pytest.mark.asyncio
async def test_get_recovery_history_not_found(session):
    """HALLUCINATION TEST: missing txn → not found, no fabricated recovery data."""
    result = await _tool_get_recovery_history(session, "NONEXISTENT_TXN_ABC")
    assert result["found"] is False
    assert "ground_truth_recoverable" not in result


@pytest.mark.asyncio
async def test_get_opportunity_found_after_leakage_run(session):
    """get_opportunity returns scored data after detect_leakage + run_scoring."""
    await _flush_batch(session, [make_record()])
    await session.commit()

    await detect_leakage(session)
    await run_scoring(session)

    result = await _tool_get_opportunity(session, "TXN10291")
    assert result["found"] is True
    assert result["revenue_at_risk"] == 15000.00
    assert result["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert result["recovery_probability"] is not None
    assert result["decision_band"] in ("GREEN", "AMBER", "RED")


@pytest.mark.asyncio
async def test_get_opportunity_not_found_returns_found_false(session):
    """
    HALLUCINATION TEST: get_opportunity for invalid txn → found=False,
    no fabricated scoring or financial data.
    """
    result = await _tool_get_opportunity(session, "TXN_NO_SUCH_OPPORTUNITY")
    assert result["found"] is False
    assert "recovery_probability" not in result
    assert "revenue_at_risk" not in result


@pytest.mark.asyncio
async def test_get_verified_metrics_aggregates_correctly(session):
    """get_verified_metrics returns accurate totals across all opportunities."""
    await _flush_batch(session, [
        make_record(transaction_id="TXN_M1", amount=5000.0, ground_truth_recovered_amount=5000.0),
        make_record(transaction_id="TXN_M2", amount=10000.0, customer_id="CUST_BBB", ground_truth_recovered_amount=10000.0),
    ])
    await session.commit()
    await detect_leakage(session)

    result = await _tool_get_verified_metrics(session)
    assert result["total_opportunities"] == 2
    assert result["total_revenue_at_risk_inr"] == pytest.approx(15000.0, abs=1.0)


# ═══════════════════════════════════════════════════════════════════════════
# DEGRADED REPORT TESTS — LLM unavailable path
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_degraded_report_with_valid_transaction(session):
    """Degraded report builds correctly from DB data when LLM is unavailable."""
    await _flush_batch(session, [make_record()])
    await session.commit()
    await detect_leakage(session)
    await run_scoring(session)

    report = await _build_degraded_report(
        session, "TXN10291", "Why is this a high opportunity?", "API key not set"
    )

    assert isinstance(report, InvestigationReport)
    assert report.llm_unavailable is True
    assert report.not_found is False
    assert report.transaction_id == "TXN10291"
    assert len(report.evidence) > 0
    # Critical: evidence must contain real DB values
    assert any("15,000" in e or "15000" in e for e in report.evidence), \
        f"Expected ₹15,000 in evidence, got: {report.evidence}"
    assert report.error_message == "API key not set"


@pytest.mark.asyncio
async def test_degraded_report_with_invalid_transaction(session):
    """
    HALLUCINATION TEST: degraded report with invalid TXN ID must return
    not_found=True and no fabricated financial data.
    """
    report = await _build_degraded_report(
        session, "TXN_TOTALLY_FAKE_9999", "Investigate this", "LLM down"
    )

    assert isinstance(report, InvestigationReport)
    assert report.not_found is True
    assert report.llm_unavailable is True
    # CRITICAL: No financial data should be present for a non-existent transaction
    assert report.revenue_impact is None
    assert report.recovery_probability is None
    # Evidence should NOT contain any monetary amounts
    for ev in report.evidence:
        assert "₹" not in ev, f"Fabricated financial data found in evidence: {ev}"


# ═══════════════════════════════════════════════════════════════════════════
# REPORT SCHEMA VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_investigation_report_schema_all_fields_optional():
    """InvestigationReport can be instantiated with minimal fields — no crashes."""
    report = InvestigationReport(
        transaction_id="TXN001",
        question="test question",
    )
    assert report.transaction_id == "TXN001"
    assert report.evidence == []
    assert report.tool_calls_log == []
    assert report.llm_unavailable is False
    assert report.not_found is False


def test_investigation_report_not_found_flag():
    """not_found flag is correctly propagated."""
    report = InvestigationReport(
        transaction_id="INVALID",
        question="Where is this?",
        not_found=True,
        evidence=["No transaction with this ID was found in the database."],
    )
    assert report.not_found is True
    assert "found in the database" in report.evidence[0].lower()


@pytest.mark.asyncio
async def test_multiple_invalid_txns_never_cross_contaminate(session):
    """
    HALLUCINATION TEST: querying multiple non-existent IDs in sequence
    must NEVER return data from one "bleed" into another response.
    """
    ids = ["FAKE_TXN_A", "FAKE_TXN_B", "FAKE_TXN_C", ""]
    for txn_id in ids:
        result = await _tool_get_transaction(session, txn_id)
        assert result["found"] is False, f"Expected not found for '{txn_id}'"
        assert "amount" not in result
        assert "customer_id" not in result


@pytest.mark.asyncio
async def test_real_txn_does_not_leak_to_different_invalid_query(session):
    """
    HALLUCINATION TEST: inserting a real transaction and then querying a
    completely different ID must return not-found, not the real transaction's data.
    """
    await _flush_batch(session, [make_record(transaction_id="TXN_REAL_001", amount=99999.0)])
    await session.commit()

    # Query a completely different ID — must NOT get TXN_REAL_001's data
    result = await _tool_get_transaction(session, "TXN_DIFFERENT_999")
    assert result["found"] is False
    assert "amount" not in result
