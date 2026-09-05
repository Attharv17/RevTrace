import pytest
from httpx import AsyncClient
from app.api.evaluation import EVAL_FILE

@pytest.mark.asyncio
async def test_get_evaluation_results_success(client: AsyncClient):
    # This assumes pipeline has been run and EVAL_FILE exists
    if not EVAL_FILE.exists():
        pytest.skip("evaluation.json not found")
        
    response = await client.get("/api/evaluation/results")
    assert response.status_code == 200
    data = response.json()
    assert "ml_justified" in data
    assert "metrics" in data
    assert "baseline" in data["metrics"]
    assert "ml" in data["metrics"]
