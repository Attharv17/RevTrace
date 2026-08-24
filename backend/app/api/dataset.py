"""
LedgerPilot — Dataset API Router
Endpoints for generating, summarising, and exporting synthetic financial data.
"""
import io
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.data.generator import SyntheticDataEngine, get_engine
from app.data.summary import compute_summary

router = APIRouter(prefix="/api/data", tags=["dataset"])

# Resolved data output directory
DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")


# ── Request / Response Models ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    seed: int = 42
    num_transactions: int = 600


class GenerateResponse(BaseModel):
    status: str
    seed: int
    num_transactions: int
    generated_at: str
    record_counts: dict
    exception_breakdown: list


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse, summary="Generate Synthetic Dataset")
async def generate_dataset(request: GenerateRequest = GenerateRequest()):
    """
    Generate a synthetic financial dataset.

    - Uses a seeded random generator for reproducibility.
    - Injects 11 exception categories into the dataset.
    - Exports CSVs to `backend/data/`.
    - Returns dataset summary.
    """
    if request.num_transactions < 100 or request.num_transactions > 10_000:
        raise HTTPException(
            status_code=422,
            detail="num_transactions must be between 100 and 10,000.",
        )

    engine = SyntheticDataEngine(
        seed=request.seed,
        num_transactions=request.num_transactions,
    )
    engine.generate()

    # Export CSVs
    os.makedirs(DATA_DIR, exist_ok=True)
    engine.export_csvs(DATA_DIR)

    # Update the module-level singleton
    import app.data.generator as gen_module
    gen_module._engine_instance = engine

    summary = compute_summary(engine)

    return GenerateResponse(
        status="generated",
        seed=engine.seed,
        num_transactions=request.num_transactions,
        generated_at=engine._generated_at or "",
        record_counts=summary["record_counts"],
        exception_breakdown=summary["exception_breakdown"],
    )


@router.get("/summary", summary="Dataset Summary Statistics")
async def get_dataset_summary():
    """
    Return rich summary statistics for the currently loaded dataset.
    Generates a default dataset (seed=42, 600 txns) if none is loaded.
    """
    engine = get_engine()
    if not engine.is_generated:
        engine.generate()
        os.makedirs(DATA_DIR, exist_ok=True)
        engine.export_csvs(DATA_DIR)

    return compute_summary(engine)


@router.get("/exceptions", summary="Exception Type Breakdown")
async def get_exception_breakdown():
    """Return exception category counts from the ground truth table."""
    engine = get_engine()
    if not engine.is_generated:
        engine.generate()
    return {
        "total": len(engine.ground_truth),
        "breakdown": engine.get_exception_breakdown(),
    }


@router.get("/export/{table}", summary="Export Table as CSV")
async def export_csv(
    table: str,
    include_ground_truth: bool = Query(
        default=False,
        description="Allow exporting the hidden ground truth table (testing only).",
    ),
):
    """
    Stream a CSV download for the specified table.

    Available tables: gateway_transactions | merchant_orders | bank_settlements | ground_truth
    """
    engine = get_engine()
    if not engine.is_generated:
        engine.generate()
        os.makedirs(DATA_DIR, exist_ok=True)
        engine.export_csvs(DATA_DIR)

    ALLOWED = {
        "gateway_transactions",
        "merchant_orders",
        "bank_settlements",
    }
    if table == "ground_truth":
        if not include_ground_truth:
            raise HTTPException(
                status_code=403,
                detail="Ground truth is hidden. Pass ?include_ground_truth=true to export.",
            )
        rows = [g.to_dict() for g in engine.ground_truth]
    elif table in ALLOWED:
        if table == "gateway_transactions":
            rows = [t.to_public_dict() for t in engine.gateway_transactions]
        elif table == "merchant_orders":
            rows = [o.to_dict() for o in engine.merchant_orders]
        else:
            rows = [s.to_dict() for s in engine.bank_settlements]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown table '{table}'. Choose from: {', '.join(ALLOWED)}.",
        )

    if not rows:
        raise HTTPException(status_code=204, detail="No data available.")

    import csv as csv_mod
    output = io.StringIO()
    writer = csv_mod.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{table}.csv"',
            "X-Record-Count": str(len(rows)),
        },
    )


@router.get("/ground-truth", summary="Ground Truth Labels (Testing Only)")
async def get_ground_truth(limit: int = Query(default=50, le=600)):
    """
    Return a sample of ground truth records for testing purposes.
    In production, this endpoint would be restricted to internal tools only.
    """
    engine = get_engine()
    if not engine.is_generated:
        engine.generate()

    sample = engine.ground_truth[:limit]
    return {
        "total": len(engine.ground_truth),
        "sample_size": len(sample),
        "records": [g.to_dict() for g in sample],
    }


@router.get("/status", summary="Dataset Status")
async def get_dataset_status():
    """Quick check on whether a dataset is currently loaded."""
    engine = get_engine()
    if not engine.is_generated:
        return {"loaded": False, "message": "No dataset generated yet."}

    return {
        "loaded": True,
        "seed": engine.seed,
        "generated_at": engine._generated_at,
        "num_transactions": len(engine.gateway_transactions),
        "num_settlements": len(engine.bank_settlements),
        "num_ground_truth": len(engine.ground_truth),
    }
