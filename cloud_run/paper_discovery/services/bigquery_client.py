import asyncio
import structlog
from typing import List, Dict, Any
from google.cloud import bigquery
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings

logger = structlog.get_logger(__name__)

class AsyncBigQueryClient:
    """Async wrapper for BigQuery operations"""
    
    def __init__(self):
        self.project_id = settings.PROJECT_ID
        self.dataset_id = settings.DATASET_ID
        self._client = None
    
    async def _get_client(self) -> bigquery.Client:
        """Lazy-load BigQuery client"""
        if self._client is None:
            self._client = await asyncio.to_thread(bigquery.Client)
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def store_papers(self, papers: List[Dict[str, Any]]) -> bool:
        """Store papers in BigQuery using async operations"""
        if not papers:
            logger.warning("No papers to store")
            return True
            
        try:
            client = await self._get_client()
            table_id = f"{self.project_id}.{self.dataset_id}.papers"
            
            logger.info("Storing papers in BigQuery", 
                       paper_count=len(papers), 
                       table_id=table_id)
            
            # Prepare job configuration
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema_update_options=[
                    bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
                ],
                ignore_unknown_values=True
            )
            
            # Run the load job in thread pool
            job = await asyncio.to_thread(
                client.load_table_from_json,
                papers,
                table_id,
                job_config=job_config
            )
            
            # Wait for job completion
            await asyncio.to_thread(job.result)
            
            logger.info("Successfully stored papers", 
                       paper_count=len(papers),
                       job_id=job.job_id)
            return True
            
        except Exception as e:
            logger.error("Failed to store papers in BigQuery", 
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def check_existing_papers(self, paper_ids: List[str]) -> List[str]:
        """Check which papers already exist in BigQuery"""
        if not paper_ids:
            return []
            
        try:
            client = await self._get_client()
            
            # Create parameterized query to avoid injection
            query = f"""
            SELECT paper_id 
            FROM `{self.project_id}.{self.dataset_id}.papers`
            WHERE paper_id IN UNNEST(@paper_ids)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("paper_ids", "STRING", paper_ids)
                ]
            )
            
            # Run query in thread pool
            query_job = await asyncio.to_thread(
                client.query,
                query,
                job_config=job_config
            )
            
            results = await asyncio.to_thread(query_job.result)
            existing_ids = [row.paper_id for row in results]
            
            logger.info("Checked existing papers", 
                       total_checked=len(paper_ids),
                       existing_count=len(existing_ids))
            
            return existing_ids
            
        except Exception as e:
            logger.error("Failed to check existing papers", error=str(e))
            # Return empty list on error - better to have duplicates than lose data
            return []
