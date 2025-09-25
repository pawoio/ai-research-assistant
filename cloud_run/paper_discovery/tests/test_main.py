import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from paper_discovery.main import app, get_arxiv_client, get_bq_client
from paper_discovery.models.paper_models import DiscoveryRequest

# Mock dependencies
@pytest.fixture
def mock_arxiv_client():
    mock = MagicMock()
    mock.fetch_papers = AsyncMock(return_value=[
        {"id": "paper1", "title": "Paper 1"},
        {"id": "paper2", "title": "Paper 2"}
    ])
    return mock

@pytest.fixture
def mock_bq_client():
    mock = MagicMock()
    mock.check_existing_papers = AsyncMock(return_value=["paper1"])
    mock.ingest_papers = AsyncMock()
    return mock

# Override dependencies in the app
@pytest.fixture
def test_client(mock_arxiv_client, mock_bq_client):
    app.dependency_overrides[get_arxiv_client] = lambda: mock_arxiv_client
    app.dependency_overrides[get_bq_client] = lambda: mock_bq_client
    return TestClient(app)

# Test health check endpoint
def test_health_check(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Test discover endpoint
@pytest.mark.asyncio
async def test_discover_papers(test_client, mock_arxiv_client, mock_bq_client):
    request_data = {
        "queries": ["machine learning"],
        "max_results_per_query": 10
    }
    response = test_client.post("/discover", json=request_data)
    assert response.status_code == 200
    response_data = response.json()
    assert "job_id" in response_data
    assert response_data["status"] == "in_progress"
    assert response_data["papers_discovered"] == 0

    # Verify background task behavior
    job_id = response_data["job_id"]
    await mock_arxiv_client.fetch_papers.assert_called_once_with("machine learning", 10)
    await mock_bq_client.check_existing_papers.assert_called_once()
    await mock_bq_client.ingest_papers.assert_called_once()

# Test discover endpoint with invalid input
def test_discover_papers_invalid_input(test_client):
    request_data = {
        "queries": [],
        "max_results_per_query": 10
    }
    response = test_client.post("/discover", json=request_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "At least one query must be provided"}

# Test job status endpoint
def test_job_status(test_client):
    # Simulate a job in progress
    job_id = "test-job-id"
    from paper_discovery.main import job_status
    job_status[job_id] = "in_progress"

    response = test_client.get(f"/status?job_id={job_id}")
    assert response.status_code == 200
    assert response.json() == {"job_id": job_id, "status": "in_progress"}

    # Simulate a completed job
    job_status[job_id] = "completed"
    response = test_client.get(f"/status?job_id={job_id}")
    assert response.status_code == 200
    assert response.json() == {"job_id": job_id, "status": "completed"}

    # Test for a non-existent job
    response = test_client.get("/status?job_id=non_existent_job")
    assert response.status_code == 200
    assert response.json() == {"job_id": "non_existent_job", "status": "not_found"}