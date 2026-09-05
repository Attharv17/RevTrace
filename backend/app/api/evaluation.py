import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas.evaluation import EvaluationReport
import subprocess

router = APIRouter(tags=["Evaluation"])

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "ml" / "artifacts"
EVAL_FILE = ARTIFACTS_DIR / "evaluation.json"

@router.get("/api/evaluation/results", response_model=EvaluationReport)
async def get_evaluation_results():
    """
    Returns the ML vs Baseline evaluation results.
    """
    if not EVAL_FILE.exists():
        raise HTTPException(status_code=404, detail="Evaluation results not found. Run the ML pipeline first.")
    
    with open(EVAL_FILE, "r") as f:
        data = json.load(f)
    
    return EvaluationReport(**data)


@router.post("/api/evaluation/run")
async def run_evaluation_pipeline():
    """
    Triggers the ML pipeline training and evaluation script.
    """
    pipeline_script = Path(__file__).resolve().parent.parent / "ml" / "pipeline.py"
    # Execute via the ML specific venv if it exists, otherwise default python
    venv_ml = Path(__file__).resolve().parent.parent.parent / ".venv-ml" / "Scripts" / "python.exe"
    python_exec = str(venv_ml) if venv_ml.exists() else "python"
    
    try:
        # Run subprocess and wait for completion
        result = subprocess.run(
            [python_exec, str(pipeline_script)],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "message": "ML pipeline executed successfully.", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e.stderr}")
