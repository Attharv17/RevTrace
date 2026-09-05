"""
RevTrace — Phase 7: AI Investigation Agent Schemas.

All schemas enforce that the LLM is a reasoning layer only.
Financial figures always trace back to DB tool call results.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    """Request body for the investigation endpoint."""
    transaction_id: str = Field(
        ...,
        description="The transaction ID to investigate (e.g. TXN10291).",
        examples=["TXN10291"],
    )
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language question about this transaction.",
        examples=["Why is this a high recovery opportunity?"],
    )


class ToolCallLog(BaseModel):
    """Audit record for a single tool call made during investigation."""
    tool_name: str
    arguments: Dict[str, Any]
    result_summary: str    # Short summary of what was returned (not the full payload)
    called_at: datetime


class InvestigationReport(BaseModel):
    """
    Structured LLM investigation report.

    IMPORTANT: All financial figures here are sourced exclusively from DB
    tool calls — the LLM does not invent or modify any values.
    """
    transaction_id: str
    question: str

    # ── Core report fields ─────────────────────────────────────────────────────
    # recovery_probability: pulled from DB scoring, not LLM-generated
    recovery_probability: Optional[float] = Field(
        None,
        description="DB-verified recovery probability from scoring engine (0.0–1.0).",
    )
    decision_band: Optional[str] = Field(
        None,
        description="DB scoring band: GREEN | AMBER | RED.",
    )

    # LLM synthesizes these from retrieved DB data only
    evidence: List[str] = Field(
        default_factory=list,
        description="Concise evidence points citing actual DB values.",
    )
    revenue_impact: Optional[str] = Field(
        None,
        description="Revenue impact statement with verified figures from DB.",
    )
    recommendation: Optional[str] = Field(
        None,
        description="Recommended recovery action, grounded in DB scoring data.",
    )
    confidence_note: Optional[str] = Field(
        None,
        description="Confidence/uncertainty note from the LLM about its assessment.",
    )

    # ── Degraded / error state ────────────────────────────────────────────────
    llm_unavailable: bool = Field(
        False,
        description="True if LLM was unavailable; report contains raw DB data only.",
    )
    not_found: bool = Field(
        False,
        description="True if transaction_id was not found in the database.",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error description if something went wrong.",
    )

    # ── Audit trail ───────────────────────────────────────────────────────────
    tool_calls_log: List[ToolCallLog] = Field(
        default_factory=list,
        description="Full audit trail of every tool call made during investigation.",
    )
    investigated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantHealthResponse(BaseModel):
    """Health check for the AI assistant subsystem."""
    llm_configured: bool
    llm_model: str
    status: str    # "ready" | "degraded" | "unavailable"
    message: str
