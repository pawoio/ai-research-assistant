import asyncio
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import structlog

from .models.paper_models import DiscoveryRequest, DiscoveryResponse
from .services.arxiv_client import ArxivClient
from .services.bigquery_client import AsyncBigQueryClient
from .config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global clients
arxiv_client = None
bq_client = None

# In-memory job status tracking (for simplicity)
job_status = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global arxiv_client, bq_client

    logger.info("Starting Paper Discovery Service")

    # Initialize clients
    try:
        arxiv_client = ArxivClient()
        bq_client = AsyncBigQueryClient()
        logger.info("Service initialization completed")
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise RuntimeError("Service initialization failed") from e

    yield

    # Cleanup resources
    try:
        await bq_client.close()
        logger.info("Shutting down Paper Discovery Service")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="AI Research Assistant - Paper Discovery Service",
    description="Discovers and ingests research papers from ArXiv",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Use config for allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for clients
def get_arxiv_client():
    return arxiv_client

def get_bq_client():
    return bq_client

# Background task for paper discovery
async def _background_paper_discovery(
    job_id: str,
    queries: List[str],
    max_results_per_query: int,
    arxiv_client: ArxivClient,
    bq_client: AsyncBigQueryClient
):
    try:
        logger.info("Starting paper discovery", job_id=job_id, queries=queries)

        # Check existing papers in BigQuery
        existing_ids = await bq_client.check_existing_papers([])
        logger.info("Fetched existing paper IDs", count=len(existing_ids))

        # Fetch papers from ArXiv
        papers = []
        for query in queries:
            try:
                results = await arxiv_client.fetch_papers(query, max_results_per_query)
                papers.extend(results)
            except Exception as e:
                logger.error("Error fetching papers for query", query=query, error=str(e))

        # Filter out existing papers
        new_papers = [paper for paper in papers if paper.id not in existing_ids]
        logger.info("Filtered new papers", count=len(new_papers))

        # Ingest new papers into BigQuery
        if new_papers:
            await bq_client.ingest_papers(new_papers)
            logger.info("Ingested new papers into BigQuery", count=len(new_papers))

        # Update job status
        job_status[job_id] = "completed"
        logger.info("Paper discovery completed", job_id=job_id)

    except Exception as e:
        logger.error("Error during paper discovery", job_id=job_id, error=str(e))
        job_status[job_id] = "failed"

# Health check endpoint
@app.get("/")
async def health_check():
    # Optionally check external services' health
    try:
        await bq_client.ping()
        return {"status": "ok"}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service is unhealthy")

# Endpoint to start paper discovery
@app.post("/discover", response_model=DiscoveryResponse)
async def discover_papers(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    arxiv_client: ArxivClient = Depends(get_arxiv_client),
    bq_client: AsyncBigQueryClient = Depends(get_bq_client)
):
    if not request.queries:
        raise HTTPException(
            status_code=400,
            detail="At least one query must be provided"
        )

    job_id = f"job-{uuid.uuid4()}"
    job_status[job_id] = "in_progress"

    background_tasks.add_task(
        _background_paper_discovery,
        job_id,
        request.queries,
        request.max_results_per_query,
        arxiv_client,
        bq_client
    )

    return DiscoveryResponse(
        job_id=job_id,
        status="in_progress",
        papers_discovered=0  # Discovery happens in the background
    )

# Endpoint to check job status
@app.get("/status")
async def get_job_status(job_id: str):
    status = job_status.get(job_id, "not_found")
    return {"job_id": job_id, "status": status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
