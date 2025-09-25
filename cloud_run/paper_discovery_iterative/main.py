from fastapi import FastAPI
from typing import Dict
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Paper Discovery Service",
    description="ArXiv paper discovery and ingestion service",
    version="0.1.0"
)

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint for basic health check"""
    return {"message": "Paper Discovery Service is running", "status": "healthy"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "paper-discovery"}

@app.get("/status")
async def status() -> Dict[str, str]:
    """Status endpoint with basic service information"""
    return {
        "status": "running",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
