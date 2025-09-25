import asyncio
import arxiv
import structlog
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from asyncio_throttle import Throttler
from datetime import datetime
from ..models.paper_models import PaperData
from ..config import settings

logger = structlog.get_logger(__name__)

class ArxivClient:
    """ArXiv client with proper rate limiting and error handling"""
    
    def __init__(self):
        # Create throttler for ArXiv rate limiting (1 call per 3 seconds)
        self.throttler = Throttler(
            rate_limit=settings.ARXIV_RATE_LIMIT_CALLS,
            period=settings.ARXIV_RATE_LIMIT_PERIOD
        )
    
    @retry(
        stop=stop_after_attempt(settings.ARXIV_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((arxiv.ArxivError, ConnectionError))
    )
    async def _fetch_papers_for_query(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers for a single query with rate limiting"""
        
        async with self.throttler:  # Enforces rate limiting
            logger.info("Fetching papers from ArXiv", query=query, max_results=max_results)
            
            try:
                # Run blocking ArXiv call in thread pool
                search = await asyncio.to_thread(
                    self._create_arxiv_search, 
                    query, 
                    max_results
                )
                
                papers = []
                # Process results in thread pool to avoid blocking
                for result in await asyncio.to_thread(list, search.results()):
                    paper_data = await self._convert_arxiv_result(result)
                    papers.append(paper_data)
                
                logger.info("Successfully fetched papers", 
                          query=query, 
                          paper_count=len(papers))
                return papers
                
            except arxiv.ArxivError as e:
                logger.error("ArXiv API error", query=query, error=str(e))
                raise
            except Exception as e:
                logger.error("Unexpected error fetching papers", 
                           query=query, 
                           error=str(e), 
                           error_type=type(e).__name__)
                raise
    
    def _create_arxiv_search(self, query: str, max_results: int) -> arxiv.Search:
        """Create ArXiv search object - runs in thread pool"""
        return arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
    
    async def _convert_arxiv_result(self, result: arxiv.Result) -> Dict[str, Any]:
        """Convert ArXiv result to our paper format"""
        try:
            paper_data = {
                'paper_id': result.entry_id,
                'title': result.title.strip(),
                'abstract': result.summary.strip() if result.summary else None,
                'authors': [str(author) for author in result.authors],
                'publication_date': result.published.date() if result.published else None,
                'venue': None,  # ArXiv doesn't provide venue info
                'arxiv_id': result.entry_id.split('/')[-1],
                'semantic_scholar_id': None,
                'categories': result.categories,
                'full_text': None,  # Would need to download PDF separately
                'created_at': datetime.utcnow()
            }
            
            # Validate using Pydantic model
            validated_paper = PaperData(**paper_data)
            return validated_paper.dict()
            
        except Exception as e:
            logger.error("Error converting ArXiv result", 
                        paper_id=getattr(result, 'entry_id', 'unknown'),
                        error=str(e))
            raise
    
    async def fetch_papers(self, queries: List[str], max_results_per_query: int = 50) -> List[Dict[str, Any]]:
        """Fetch papers for multiple queries concurrently (with rate limiting)"""
        logger.info("Starting paper discovery", 
                   query_count=len(queries), 
                   max_results_per_query=max_results_per_query)
        
        # Create tasks for concurrent execution (but rate-limited)
        tasks = [
            self._fetch_papers_for_query(query, max_results_per_query)
            for query in queries
        ]
        
        # Execute all queries concurrently but with rate limiting
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        all_papers = []
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                logger.error("Query failed", 
                           query=queries[i], 
                           error=str(result))
                continue
            all_papers.extend(result)
        
        # Remove duplicates based on paper_id
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper['paper_id'] not in seen_ids:
                seen_ids.add(paper['paper_id'])
                unique_papers.append(paper)
        
        logger.info("Paper discovery completed", 
                   total_papers=len(unique_papers),
                   duplicates_removed=len(all_papers) - len(unique_papers))
        
        
        return unique_papers
