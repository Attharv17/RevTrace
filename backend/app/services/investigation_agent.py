"""
RevTrace — Phase 7: AI Investigation Agent Service.

Architecture:
  1. Six read-only DB tool functions retrieve verified data.
  2. The LLM (Gemini) calls those tools via function-calling.
  3. Tool results are fed back to the model — it cannot invent values.
  4. A structured InvestigationReport is returned; chain-of-thought is never exposed.

Constraints enforced by design:
  - All 6 tools are SELECT-only; no INSERT / UPDATE / DELETE possible.
  - The system prompt hard-prohibits inventing transactions, amounts, or history.
  - If the LLM is unavailable, a degraded report with raw DB data is returned.
  - Tool call results are logged in full for the audit trail.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial import Customer, PaymentAttempt, Transaction
from app.models.opportunity import RecoveryOpportunity
from app.schemas.investigation import InvestigationReport, ToolCallLog

logger = logging.getLogger(__name__)

# ── System prompt — grounding constraints ─────────────────────────────────────

SYSTEM_PROMPT = """You are RevTrace Investigation Agent, a read-only financial analyst.

STRICT RULES — violation is not permitted under any circumstance:
1. You MUST call the available tools to retrieve data before answering.
2. You MUST NOT invent, guess, or fabricate any transaction IDs, customer IDs, amounts, dates, or history.
3. You MUST NOT expose your internal reasoning or chain-of-thought.
4. You MUST NOT modify any records, balances, or recovery statuses.
5. You MUST NOT directly execute any recovery action.
6. If a tool returns no data, state clearly that the record was not found. Do not invent alternatives.
7. Every figure you cite MUST trace back to a tool call result in this conversation.

RESPONSE FORMAT:
Return a JSON object with exactly these fields (no extra fields):
{
  "evidence": ["<point 1>", "<point 2>", ...],
  "revenue_impact": "<verified revenue impact statement with exact figures>",
  "recommendation": "<recovery action grounded in DB data>",
  "confidence_note": "<honest assessment of confidence level and any data gaps>"
}

Do not include markdown, explanations, or any text outside the JSON object.
"""

# ── Tool definitions for Gemini function-calling ─────────────────────────────

TOOL_DECLARATIONS = [
    {
        "name": "get_transaction",
        "description": (
            "Retrieve full details of a single transaction by its transaction_id. "
            "Returns payment status, amount, currency, failure reason, payment method, "
            "retry count, payment history, and ground truth labels."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction ID to look up (e.g. TXN10291).",
                }
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_customer_history",
        "description": (
            "Retrieve aggregated payment history for the customer associated with "
            "the given transaction_id. Returns total transactions, success rate, "
            "failure patterns, and whether they have previously recovered payments."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "Look up the customer linked to this transaction.",
                }
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_payment_attempts",
        "description": (
            "Retrieve all payment recovery attempts made for a transaction. "
            "Returns each attempt's action, outcome, recovered amount, and timestamp."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction ID to look up attempts for.",
                }
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_recovery_history",
        "description": (
            "Retrieve the ground truth recovery information for a transaction: "
            "whether it is recoverable, the recommended recovery action, "
            "the expected recovered amount, and the reason label."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction ID to retrieve recovery history for.",
                }
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_opportunity",
        "description": (
            "Retrieve the RecoveryOpportunity record for a transaction: "
            "revenue at risk, scoring data (recovery_probability, decision_band, "
            "recommended_action, priority), severity, and current status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction ID to retrieve the opportunity for.",
                }
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_verified_metrics",
        "description": (
            "Retrieve aggregate financial metrics across all opportunities: "
            "total revenue at risk, total recoverable amount, counts by severity "
            "and status. Useful for contextualising how a specific opportunity "
            "compares to the overall portfolio."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Read-only tool implementations (DB queries only) ─────────────────────────

async def _tool_get_transaction(
    session: AsyncSession,
    transaction_id: str,
) -> Dict[str, Any]:
    """SELECT-only: fetch one transaction by ID."""
    result = await session.execute(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
    )
    txn = result.scalar_one_or_none()
    if txn is None:
        return {"found": False, "transaction_id": transaction_id}
    return {
        "found": True,
        "transaction_id": txn.transaction_id,
        "customer_id": txn.customer_id,
        "merchant_id": txn.merchant_id,
        "amount": txn.amount,
        "currency": txn.currency,
        "payment_method": txn.payment_method,
        "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,
        "payment_status": txn.payment_status,
        "failure_reason": txn.failure_reason,
        "retry_count": txn.retry_count,
        "previous_payment_history": txn.previous_payment_history,
        "recurring_payment": txn.recurring_payment,
        "refund_status": txn.refund_status,
    }


async def _tool_get_customer_history(
    session: AsyncSession,
    transaction_id: str,
) -> Dict[str, Any]:
    """SELECT-only: aggregate customer transactions by looking up via transaction."""
    # First get the customer_id from the transaction
    result = await session.execute(
        select(Transaction.customer_id).where(Transaction.transaction_id == transaction_id)
    )
    customer_id = result.scalar_one_or_none()
    if customer_id is None:
        return {"found": False, "transaction_id": transaction_id}

    # Aggregate all transactions for this customer
    all_txns = await session.execute(
        select(Transaction).where(Transaction.customer_id == customer_id)
    )
    txns = all_txns.scalars().all()
    if not txns:
        return {"found": False, "customer_id": customer_id}

    total = len(txns)
    successful = sum(1 for t in txns if t.payment_status == "success")
    failed = sum(1 for t in txns if t.payment_status == "failed")
    failure_reasons = list({t.failure_reason for t in txns if t.failure_reason})
    payment_methods = list({t.payment_method for t in txns})
    avg_amount = round(sum(t.amount for t in txns) / total, 2)

    # Count previous recoveries from payment attempts
    attempts_result = await session.execute(
        select(PaymentAttempt.recovery_outcome).where(
            PaymentAttempt.transaction_id.in_([t.transaction_id for t in txns])
        )
    )
    outcomes = [row[0] for row in attempts_result.all()]
    successful_recoveries = sum(1 for o in outcomes if o == "success")

    return {
        "found": True,
        "customer_id": customer_id,
        "total_transactions": total,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "success_rate_pct": round(successful / total * 100, 1) if total else 0,
        "failure_reasons_seen": failure_reasons,
        "payment_methods_used": payment_methods,
        "average_transaction_amount_inr": avg_amount,
        "previous_successful_recoveries": successful_recoveries,
        "payment_history_label": txns[0].previous_payment_history if txns else None,
    }


async def _tool_get_payment_attempts(
    session: AsyncSession,
    transaction_id: str,
) -> Dict[str, Any]:
    """SELECT-only: fetch all payment attempts for a transaction."""
    result = await session.execute(
        select(PaymentAttempt).where(PaymentAttempt.transaction_id == transaction_id)
    )
    attempts = result.scalars().all()
    return {
        "transaction_id": transaction_id,
        "total_attempts": len(attempts),
        "attempts": [
            {
                "id": a.id,
                "recovery_action": a.recovery_action,
                "recovery_outcome": a.recovery_outcome,
                "recovered_amount": a.recovered_amount,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in attempts
        ],
    }


async def _tool_get_recovery_history(
    session: AsyncSession,
    transaction_id: str,
) -> Dict[str, Any]:
    """SELECT-only: fetch ground truth recovery fields from the transaction."""
    result = await session.execute(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
    )
    txn = result.scalar_one_or_none()
    if txn is None:
        return {"found": False, "transaction_id": transaction_id}
    return {
        "found": True,
        "transaction_id": transaction_id,
        "ground_truth_recoverable": txn.ground_truth_recoverable,
        "ground_truth_recovery_action": txn.ground_truth_recovery_action,
        "ground_truth_recovered_amount": txn.ground_truth_recovered_amount,
        "ground_truth_reason": txn.ground_truth_reason,
    }


async def _tool_get_opportunity(
    session: AsyncSession,
    transaction_id: str,
) -> Dict[str, Any]:
    """SELECT-only: fetch the RecoveryOpportunity record."""
    result = await session.execute(
        select(RecoveryOpportunity).where(
            RecoveryOpportunity.transaction_id == transaction_id
        )
    )
    opp = result.scalar_one_or_none()
    if opp is None:
        return {"found": False, "transaction_id": transaction_id}
    return {
        "found": True,
        "opportunity_id": opp.id,
        "transaction_id": opp.transaction_id,
        "expected_revenue": opp.expected_revenue,
        "realized_revenue": opp.realized_revenue,
        "revenue_at_risk": opp.revenue_at_risk,
        "recoverable_amount": opp.recoverable_amount,
        "reason": opp.reason,
        "severity": opp.severity,
        "status": opp.status,
        "recovery_probability": opp.recovery_probability,
        "expected_recovery": opp.expected_recovery,
        "priority": opp.priority,
        "recommended_action": opp.recommended_action,
        "decision_band": opp.decision_band,
        "score_version": opp.score_version,
        "detected_at": opp.detected_at.isoformat() if opp.detected_at else None,
    }


async def _tool_get_verified_metrics(
    session: AsyncSession,
) -> Dict[str, Any]:
    """SELECT-only: aggregate portfolio metrics."""
    result = await session.execute(
        select(
            func.count(RecoveryOpportunity.id),
            func.sum(RecoveryOpportunity.revenue_at_risk),
            func.sum(RecoveryOpportunity.recoverable_amount),
        )
    )
    row = result.one()
    total, at_risk, recoverable = row

    def _count(status=None, severity=None):
        q = select(func.count(RecoveryOpportunity.id))
        if status:
            q = q.where(RecoveryOpportunity.status == status)
        if severity:
            q = q.where(RecoveryOpportunity.severity == severity)
        return q

    pending_r = (await session.execute(_count(status="pending"))).scalar_one()
    critical_r = (await session.execute(_count(severity="CRITICAL"))).scalar_one()
    high_r = (await session.execute(_count(severity="HIGH"))).scalar_one()

    return {
        "total_opportunities": total or 0,
        "total_revenue_at_risk_inr": round(at_risk or 0, 2),
        "total_recoverable_amount_inr": round(recoverable or 0, 2),
        "pending_opportunities": pending_r,
        "critical_opportunities": critical_r,
        "high_opportunities": high_r,
    }


# ── Tool dispatcher ───────────────────────────────────────────────────────────

async def _dispatch_tool(
    session: AsyncSession,
    tool_name: str,
    args: Dict[str, Any],
) -> Any:
    """Route a tool call name to the correct DB function."""
    if tool_name == "get_transaction":
        return await _tool_get_transaction(session, **args)
    elif tool_name == "get_customer_history":
        return await _tool_get_customer_history(session, **args)
    elif tool_name == "get_payment_attempts":
        return await _tool_get_payment_attempts(session, **args)
    elif tool_name == "get_recovery_history":
        return await _tool_get_recovery_history(session, **args)
    elif tool_name == "get_opportunity":
        return await _tool_get_opportunity(session, **args)
    elif tool_name == "get_verified_metrics":
        return await _tool_get_verified_metrics(session)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ── Degraded report builder (no LLM) ─────────────────────────────────────────

async def _build_degraded_report(
    session: AsyncSession,
    transaction_id: str,
    question: str,
    error_msg: str,
) -> InvestigationReport:
    """
    Build a report from raw DB data when the LLM is unavailable.
    Financial data is still accurate — just no LLM synthesis.
    """
    txn_data = await _tool_get_transaction(session, transaction_id)
    opp_data = await _tool_get_opportunity(session, transaction_id)
    attempts_data = await _tool_get_payment_attempts(session, transaction_id)

    if not txn_data.get("found"):
        return InvestigationReport(
            transaction_id=transaction_id,
            question=question,
            not_found=True,
            llm_unavailable=True,
            error_message=error_msg,
        )

    evidence = []
    if txn_data.get("found"):
        evidence.append(
            f"Transaction {transaction_id}: "
            f"₹{txn_data['amount']:,.2f} {txn_data['currency']} via {txn_data['payment_method']} "
            f"— status: {txn_data['payment_status']}"
        )
        if txn_data.get("failure_reason"):
            evidence.append(f"Failure reason: {txn_data['failure_reason']}")

    recovery_probability = None
    decision_band = None
    revenue_impact = None
    recommendation = None

    if opp_data.get("found"):
        recovery_probability = opp_data.get("recovery_probability")
        decision_band = opp_data.get("decision_band")
        evidence.append(
            f"Revenue at risk: ₹{opp_data['revenue_at_risk']:,.2f} "
            f"(severity: {opp_data['severity']})"
        )
        revenue_impact = (
            f"₹{opp_data['revenue_at_risk']:,.2f} at risk out of "
            f"₹{opp_data['expected_revenue']:,.2f} expected."
        )
        recommendation = opp_data.get("recommended_action")

    if attempts_data["total_attempts"] > 0:
        evidence.append(
            f"{attempts_data['total_attempts']} recovery attempt(s) on record."
        )

    return InvestigationReport(
        transaction_id=transaction_id,
        question=question,
        recovery_probability=recovery_probability,
        decision_band=decision_band,
        evidence=evidence,
        revenue_impact=revenue_impact,
        recommendation=recommendation,
        confidence_note="LLM synthesis unavailable — raw DB data shown.",
        llm_unavailable=True,
        error_message=error_msg,
        tool_calls_log=[
            ToolCallLog(
                tool_name="get_transaction",
                arguments={"transaction_id": transaction_id},
                result_summary="found" if txn_data.get("found") else "not found",
                called_at=datetime.now(timezone.utc),
            ),
            ToolCallLog(
                tool_name="get_opportunity",
                arguments={"transaction_id": transaction_id},
                result_summary="found" if opp_data.get("found") else "not found",
                called_at=datetime.now(timezone.utc),
            ),
        ],
    )


# ── Main investigation entry point ────────────────────────────────────────────

async def investigate(
    session: AsyncSession,
    transaction_id: str,
    question: str,
    gemini_api_key: str,
    gemini_model: str = "gemini-2.0-flash",
) -> InvestigationReport:
    """
    Orchestrate an LLM-powered investigation of a recovery opportunity.

    The LLM is NOT the source of financial truth. It calls read-only tools
    that retrieve verified DB data, then synthesizes a grounded report.

    Uses google-genai SDK (the current supported Google GenAI Python SDK).

    Args:
        session: Database session (read-only queries only).
        transaction_id: The transaction to investigate.
        question: Natural language question from the user.
        gemini_api_key: Gemini API key; if empty, returns degraded report.
        gemini_model: Gemini model name to use.

    Returns:
        InvestigationReport — always structured, never raw LLM text.
    """
    if not gemini_api_key or gemini_api_key.strip() == "":
        logger.warning("Gemini API key not configured — returning degraded report.")
        return await _build_degraded_report(
            session, transaction_id, question,
            "LLM not configured. Set GEMINI_API_KEY in backend/.env to enable AI synthesis."
        )

    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        logger.error("google-genai not installed.")
        return await _build_degraded_report(
            session, transaction_id, question,
            "google-genai package not installed. Run: pip install google-genai"
        )

    client = genai.Client(api_key=gemini_api_key)

    # Build function declarations for Gemini function-calling
    function_declarations = []
    for decl in TOOL_DECLARATIONS:
        function_declarations.append(
            genai_types.FunctionDeclaration(
                name=decl["name"],
                description=decl["description"],
                parameters=genai_types.Schema(
                    type=genai_types.Type.OBJECT,
                    properties={
                        k: genai_types.Schema(
                            type=genai_types.Type.STRING,
                            description=v.get("description", ""),
                        )
                        for k, v in decl["parameters"].get("properties", {}).items()
                    },
                    required=decl["parameters"].get("required", []),
                ) if decl["parameters"].get("properties") else None,
            )
        )

    tools = [genai_types.Tool(function_declarations=function_declarations)]
    config = genai_types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
    )

    # Build the initial user message
    user_message = (
        f"Investigate transaction ID: {transaction_id}\n"
        f"Question: {question}\n\n"
        f"Use the available tools to retrieve all relevant data, then answer the question "
        f"with a structured JSON report."
    )

    tool_calls_log: List[ToolCallLog] = []
    opp_data_cache: Optional[Dict[str, Any]] = None

    try:
        # Build conversation history
        contents: List[genai_types.Content] = [
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=user_message)],
            )
        ]

        MAX_ROUNDS = 8
        rounds = 0

        while rounds < MAX_ROUNDS:
            rounds += 1

            # Call the model
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda c=contents: client.models.generate_content(
                    model=gemini_model,
                    contents=c,
                    config=config,
                ),
            )

            # Append model response to history
            contents.append(response.candidates[0].content)

            # Check for function calls
            function_calls_in_response = [
                part.function_call
                for part in response.candidates[0].content.parts
                if part.function_call is not None
            ]

            if not function_calls_in_response:
                # No more tool calls — model is done
                break

            # Execute tool calls and build function response parts
            function_response_parts = []
            for fc in function_calls_in_response:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                result = await _dispatch_tool(session, tool_name, tool_args)

                # Cache opportunity data for report metadata
                if tool_name == "get_opportunity" and result.get("found"):
                    opp_data_cache = result

                tool_calls_log.append(
                    ToolCallLog(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result_summary=_summarize_result(tool_name, result),
                        called_at=datetime.now(timezone.utc),
                    )
                )

                function_response_parts.append(
                    genai_types.Part(
                        function_response=genai_types.FunctionResponse(
                            name=tool_name,
                            response={"result": json.dumps(result, default=str)},
                        )
                    )
                )

            # Add function responses to conversation
            contents.append(
                genai_types.Content(
                    role="user",
                    parts=function_response_parts,
                )
            )

        # Extract final text response
        final_text = ""
        try:
            for part in response.candidates[0].content.parts:
                if part.text:
                    final_text += part.text
        except Exception:
            pass

        report_dict = _parse_llm_json(final_text)

        # Fetch opportunity data if not already retrieved via tools
        if opp_data_cache is None:
            opp_data_cache = await _tool_get_opportunity(session, transaction_id)

        # Check if TXN was found (via tool calls or direct DB check)
        txn_found_via_tools = any(
            log.tool_name == "get_transaction" and "not found" not in log.result_summary
            for log in tool_calls_log
        )
        if not txn_found_via_tools and not tool_calls_log:
            txn_check = await _tool_get_transaction(session, transaction_id)
            if not txn_check.get("found"):
                return InvestigationReport(
                    transaction_id=transaction_id,
                    question=question,
                    not_found=True,
                    evidence=["No transaction with this ID was found in the database."],
                    tool_calls_log=tool_calls_log,
                )

        return InvestigationReport(
            transaction_id=transaction_id,
            question=question,
            recovery_probability=opp_data_cache.get("recovery_probability") if opp_data_cache else None,
            decision_band=opp_data_cache.get("decision_band") if opp_data_cache else None,
            evidence=report_dict.get("evidence", []),
            revenue_impact=report_dict.get("revenue_impact"),
            recommendation=report_dict.get("recommendation"),
            confidence_note=report_dict.get("confidence_note"),
            tool_calls_log=tool_calls_log,
        )

    except Exception as exc:
        logger.error("Gemini investigation failed: %s", exc, exc_info=True)
        return await _build_degraded_report(
            session, transaction_id, question,
            f"LLM error: {type(exc).__name__}: {str(exc)[:200]}"
        )


# ── Gemini async helpers ──────────────────────────────────────────────────────

import asyncio

async def _async_send(chat, message: str):
    """Send a message to the chat in a thread (Gemini SDK is synchronous)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: chat.send_message(message))


async def _async_send_tool_results(chat, tool_results: List[Dict]) -> Any:
    """Feed tool results back to the model."""
    import google.generativeai as genai

    parts = []
    for tr in tool_results:
        parts.append(
            genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=tr["name"],
                    response={"result": tr["response"]},
                )
            )
        )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: chat.send_message(parts))


def _extract_function_calls(response) -> List[Dict[str, Any]]:
    """Extract function call requests from a Gemini response."""
    calls = []
    try:
        for part in response.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                calls.append({
                    "name": fc.name,
                    "args": dict(fc.args),
                })
    except Exception:
        pass
    return calls


def _extract_text(response) -> str:
    """Extract text content from a Gemini response."""
    try:
        return response.text
    except Exception:
        try:
            for part in response.parts:
                if hasattr(part, "text") and part.text:
                    return part.text
        except Exception:
            pass
    return "{}"


def _summarize_result(tool_name: str, result: Dict[str, Any]) -> str:
    """Create a brief human-readable summary of a tool result."""
    if "found" in result and result["found"] is False:
        return "not found (id not in DB)"
    if tool_name == "get_transaction":
        if result.get("found"):
            return f"₹{result.get('amount', 0):,.2f} {result.get('currency', '')} — {result.get('payment_status', '')}"
    elif tool_name == "get_opportunity":
        if result.get("found"):
            return (
                f"₹{result.get('revenue_at_risk', 0):,.2f} at risk, "
                f"band: {result.get('decision_band', 'N/A')}, "
                f"prob: {result.get('recovery_probability', 'N/A')}"
            )
    elif tool_name == "get_payment_attempts":
        return f"{result.get('total_attempts', 0)} attempt(s)"
    elif tool_name == "get_customer_history":
        if result.get("found"):
            return f"{result.get('total_transactions', 0)} total txns, {result.get('success_rate_pct', 0)}% success"
    elif tool_name == "get_verified_metrics":
        return f"₹{result.get('total_revenue_at_risk_inr', 0):,.2f} total at risk"
    return "ok"


def _parse_llm_json(text: str) -> Dict[str, Any]:
    """
    Parse the LLM's JSON response safely.
    Strips markdown code fences if present.
    Falls back to empty dict on parse failure.
    """
    if not text:
        return {}
    # Strip markdown fences
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last fence lines
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        parsed = json.loads(cleaned)
        # Sanitize: ensure evidence is a list of strings
        if "evidence" in parsed and not isinstance(parsed["evidence"], list):
            parsed["evidence"] = [str(parsed["evidence"])]
        return parsed
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response: %r", text[:200])
        return {
            "evidence": ["Could not parse LLM response — see raw data from tool calls."],
            "revenue_impact": None,
            "recommendation": None,
            "confidence_note": "Parse error in LLM response format.",
        }
