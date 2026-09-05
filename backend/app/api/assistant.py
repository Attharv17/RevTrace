"""
RevTrace — Phase 7: AI Investigation Agent API endpoints.

POST /api/assistant/investigate  — Submit a question about a transaction
GET  /api/assistant/health       — Check LLM availability
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.schemas.investigation import (
    AssistantHealthResponse,
    InvestigationReport,
    InvestigationRequest,
)
from app.services.investigation_agent import investigate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Assistant"])

settings = get_settings()


@router.get(
    "/api/assistant/health",
    response_model=AssistantHealthResponse,
    summary="Check AI assistant availability",
)
async def assistant_health():
    """
    Check whether the AI investigation agent is fully configured.
    Returns status='ready' if GEMINI_API_KEY is set, 'degraded' otherwise.
    The endpoint itself is always available — the assistant degrades gracefully.
    """
    has_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip())
    return AssistantHealthResponse(
        llm_configured=has_key,
        llm_model=settings.gemini_model,
        status="ready" if has_key else "degraded",
        message=(
            f"Gemini {settings.gemini_model} ready."
            if has_key
            else "No GEMINI_API_KEY configured. Set it in backend/.env to enable LLM synthesis. "
                 "The assistant will return raw DB data in degraded mode."
        ),
    )


@router.post(
    "/api/assistant/investigate",
    response_model=InvestigationReport,
    summary="Investigate a transaction with the AI agent",
)
async def investigate_transaction(
    request: InvestigationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Submit a natural-language question about a specific transaction.

    The LLM investigation agent:
    - Calls read-only structured tools to retrieve verified DB data
    - Synthesizes a grounded report from that data only
    - Never invents transactions, amounts, or history
    - Returns a structured report with evidence citations

    If the LLM is unavailable (no API key), returns raw DB data with
    llm_unavailable=True — no hallucination, no crash.
    """
    try:
        report = await investigate(
            session=session,
            transaction_id=request.transaction_id.strip(),
            question=request.question.strip(),
            gemini_api_key=settings.gemini_api_key,
            gemini_model=settings.gemini_model,
        )
        return report
    except Exception as exc:
        logger.error(
            "Investigation endpoint error for %s: %s",
            request.transaction_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed unexpectedly: {str(exc)[:200]}"
        )
