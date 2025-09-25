import hashlib
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from collections import Counter

from ..models.paper_models import PaperData, ProcessedPaper, ProcessingStats, QualityScore
from ..config import settings

logger = structlog.get_logger(__name__)

@dataclass
class ProcessingResult:
    """Result of paper processing operation"""
    processed_papers: List[Dict[str, Any]]
    duplicates_removed: int
    quality_filtered: int
    enriched_count: int
    processing_stats: Dict[str, Any]

class PaperProcessor:
    """
    Centralized paper processing logic including:
    - Deduplication
    - Quality assessment
    - Data enrichment
    - Standardization
    """
    
    def __init__(self):
        self.quality_thresholds = {
            'min_title_length': 10,
            'min_abstract_length': 100,
            'max_title_length': 500,
            'max_abstract_length': 10000,
            'required_categories': settings.RELEVANT_CATEGORIES
        }
        
    async def process_papers(
        self, 
        raw_papers: List[Dict[str, Any]],
        existing_paper_ids: Optional[Set[str]] = None
    ) -> ProcessingResult:
        """
        Main processing pipeline for discovered papers
        
        Args:
            raw_papers: Raw paper data from ArXiv
            existing_paper_ids: Set of paper IDs already in database
            
        Returns:
            ProcessingResult with processed papers and statistics
        """
        logger.info("Starting paper processing pipeline", 
                   input_count=len(raw_papers))
        
        start_time = datetime.utcnow()
        
        # Step 1: Basic validation and cleanup
        validated_papers = await self._validate_and_clean_papers(raw_papers)
        logger.info("Papers validated", 
                   input_count=len(raw_papers),
                   validated_count=len(validated_papers))
        
        # Step 2: Remove duplicates (internal and against existing)
        deduplicated_papers = await self._deduplicate_papers(
            validated_papers, 
            existing_paper_ids or set()
        )
        duplicates_removed = len(validated_papers) - len(deduplicated_papers)
        
        # Step 3: Quality assessment and filtering
        quality_filtered_papers = await self._assess_and_filter_quality(
            deduplicated_papers
        )
        quality_filtered = len(deduplicated_papers) - len(quality_filtered_papers)
        
        # Step 4: Data enrichment
        enriched_papers = await self._enrich_paper_data(quality_filtered_papers)
        
        # Step 5: Final standardization for storage
        final_papers = await self._standardize_for_storage(enriched_papers)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        processing_stats = {
            'processing_time_seconds': processing_time,
            'input_papers': len(raw_papers),
            'validated_papers': len(validated_papers),
            'deduplicated_papers': len(deduplicated_papers),
            'quality_filtered_papers': len(quality_filtered_papers),
            'final_papers': len(final_papers),
            'duplicates_removed': duplicates_removed,
            'quality_filtered_out': quality_filtered,
            'enrichment_applied': len(enriched_papers),
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Paper processing completed", **processing_stats)
        
        return ProcessingResult(
            processed_papers=final_papers,
            duplicates_removed=duplicates_removed,
            quality_filtered=quality_filtered,
            enriched_count=len(enriched_papers),
            processing_stats=processing_stats
        )
    
    async def _validate_and_clean_papers(
        self, 
        raw_papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and clean raw paper data"""
        
        validated_papers = []
        
        for paper in raw_papers:
            try:
                # Basic required field validation
                if not paper.get('paper_id') or not paper.get('title'):
                    logger.warning("Paper missing required fields", 
                                 paper_id=paper.get('paper_id', 'unknown'))
                    continue
                
                # Clean and standardize text fields
                cleaned_paper = await self._clean_paper_text(paper)
                
                # Validate using Pydantic model
                validated_paper = PaperData(**cleaned_paper)
                validated_papers.append(validated_paper.dict())
                
            except Exception as e:
                logger.error("Paper validation failed", 
                           paper_id=paper.get('paper_id', 'unknown'),
                           error=str(e))
                continue
        
        return validated_papers
    
    async def _clean_paper_text(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize text fields"""
        
        cleaned = paper.copy()
        
        # Clean title
        if cleaned.get('title'):
            cleaned['title'] = self._clean_text(cleaned['title'])
            # Remove common ArXiv title prefixes
            cleaned['title'] = re.sub(r'^(arXiv:|arxiv:)\s*', '', cleaned['title'], flags=re.IGNORECASE)
        
        # Clean abstract
        if cleaned.get('abstract'):
            cleaned['abstract'] = self._clean_text(cleaned['abstract'])
        
        # Standardize author names
        if cleaned.get('authors'):
            cleaned['authors'] = [self._clean_author_name(author) for author in cleaned['authors']]
        
        # Clean and standardize categories
        if cleaned.get('categories'):
            cleaned['categories'] = self._standardize_categories(cleaned['categories'])
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Clean and standardize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common artifacts
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Remove HTML entities and tags (if any)
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()
    
    def _clean_author_name(self, author: str) -> str:
        """Standardize author name format"""
        if not author:
            return ""
        
        # Remove extra whitespace
        author = re.sub(r'\s+', ' ', author.strip())
        
        # Handle "Last, First" format consistently
        if ',' in author:
            parts = [part.strip() for part in author.split(',')]
            if len(parts) == 2:
                return f"{parts[1]} {parts[0]}"
        
        return author
    
    def _standardize_categories(self, categories: List[str]) -> List[str]:
        """Standardize ArXiv category format"""
        standardized = []
        
        for cat in categories:
            if not cat:
                continue
                
            # Convert to lowercase and clean
            cat = cat.lower().strip()
            
            # Map common variations to standard categories
            category_mapping = {
                'cs.ai': 'cs.AI',
                'cs.lg': 'cs.LG', 
                'cs.ir': 'cs.IR',
                'cs.cv': 'cs.CV',
                'cs.cl': 'cs.CL',
                'stat.ml': 'stat.ML'
            }
            
            standardized_cat = category_mapping.get(cat, cat.upper())
            if standardized_cat not in standardized:
                standardized.append(standardized_cat)
        
        return standardized
    
    async def _deduplicate_papers(
        self, 
        papers: List[Dict[str, Any]], 
        existing_ids: Set[str]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on various criteria"""
        
        deduplicated = []
        seen_ids = set(existing_ids)  # Start with existing paper IDs
        seen_hashes = set()
        
        for paper in papers:
            paper_id = paper['paper_id']
            
            # Skip if already exists in database
            if paper_id in seen_ids:
                logger.debug("Skipping existing paper", paper_id=paper_id)
                continue
            
            # Create content hash for duplicate detection
            content_hash = self._create_content_hash(paper)
            
            # Skip if content is duplicate
            if content_hash in seen_hashes:
                logger.debug("Skipping duplicate content", 
                           paper_id=paper_id,
                           content_hash=content_hash[:8])
                continue
            
            # Check for near-duplicate titles
            if await self._is_near_duplicate_title(paper['title'], deduplicated):
                logger.debug("Skipping near-duplicate title", paper_id=paper_id)
                continue
            
            seen_ids.add(paper_id)
            seen_hashes.add(content_hash)
            deduplicated.append(paper)
        
        return deduplicated
    
    def _create_content_hash(self, paper: Dict[str, Any]) -> str:
        """Create hash for content-based deduplication"""
        
        # Combine title and abstract for hashing
        content_parts = [
            paper.get('title', '').lower(),
            paper.get('abstract', '').lower()[:500],  # First 500 chars of abstract
            '|'.join(sorted(paper.get('authors', []))),
        ]
        
        content_string = '|'.join(filter(None, content_parts))
        return hashlib.md5(content_string.encode('utf-8')).hexdigest()
    
    async def _is_near_duplicate_title(
        self, 
        title: str, 
        existing_papers: List[Dict[str, Any]]
    ) -> bool:
        """Check if title is very similar to existing papers"""
        
        if not title or len(title) < 10:
            return False
        
        title_words = set(title.lower().split())
        
        for existing_paper in existing_papers:
            existing_title = existing_paper.get('title', '')
            if not existing_title:
                continue
            
            existing_words = set(existing_title.lower().split())
            
            # Calculate Jaccard similarity
            intersection = title_words.intersection(existing_words)
            union = title_words.union(existing_words)
            
            if union and len(intersection) / len(union) > 0.8:  # 80% similarity threshold
                return True
        
        return False
    
    async def _assess_and_filter_quality(
        self, 
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assess paper quality and filter low-quality papers"""
        
        quality_papers = []
        
        for paper in papers:
            quality_score = await self._calculate_quality_score(paper)
            
            # Add quality score to paper data
            paper['quality_score'] = quality_score.dict()
            
            # Filter based on overall quality
            if quality_score.overall_score >= settings.MIN_QUALITY_SCORE:
                quality_papers.append(paper)
            else:
                logger.debug("Paper filtered for low quality", 
                           paper_id=paper['paper_id'],
                           overall_score=quality_score.overall_score)
        
        return quality_papers
    
    async def _calculate_quality_score(self, paper: Dict[str, Any]) -> 'QualityScore':
        """Calculate comprehensive quality score for a paper"""
        
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        authors = paper.get('authors', [])
        categories = paper.get('categories', [])
        
        # Title quality (0-1)
        title_score = self._score_title_quality(title)
        
        # Abstract quality (0-1)
        abstract_score = self._score_abstract_quality(abstract)
        
        # Author credibility (0-1)
        author_score = self._score_author_credibility(authors)
        
        # Category relevance (0-1)
        category_score = self._score_category_relevance(categories)
        
        # Publication recency (0-1)
        recency_score = self._score_publication_recency(paper.get('publication_date'))
        
        # Overall weighted score
        weights = {
            'title': 0.25,
            'abstract': 0.30,
            'authors': 0.15,
            'categories': 0.20,
            'recency': 0.10
        }
        
        overall_score = (
            weights['title'] * title_score +
            weights['abstract'] * abstract_score +
            weights['authors'] * author_score +
            weights['categories'] * category_score +
            weights['recency'] * recency_score
        )
        
        return QualityScore(
            title_score=title_score,
            abstract_score=abstract_score,
            author_score=author_score,
            category_score=category_score,
            recency_score=recency_score,
            overall_score=overall_score
        )
    
    def _score_title_quality(self, title: str) -> float:
        """Score title quality based on length, clarity, etc."""
        if not title:
            return 0.0
        
        score = 0.0
        
        # Length check
        if self.quality_thresholds['min_title_length'] <= len(title) <= self.quality_thresholds['max_title_length']:
            score += 0.4
        
        # Avoid overly generic titles
        generic_patterns = [
            r'^(a|an|the)\s+(study|analysis|review|survey|approach|method)\s+of',
            r'^(towards?|on)\s+',
            r'^(improving|enhancing|optimizing)\s+'
        ]
        
        if not any(re.search(pattern, title.lower()) for pattern in generic_patterns):
            score += 0.3
        
        # Prefer titles with specific technical terms
        technical_terms = [
            'algorithm', 'model', 'neural', 'deep', 'machine learning', 
            'optimization', 'classification', 'regression', 'clustering'
        ]
        
        if any(term in title.lower() for term in technical_terms):
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_abstract_quality(self, abstract: str) -> float:
        """Score abstract quality"""
        if not abstract:
            return 0.0
        
        score = 0.0
        
        # Length check
        if self.quality_thresholds['min_abstract_length'] <= len(abstract) <= self.quality_thresholds['max_abstract_length']:
            score += 0.4
        
        # Check for key sections (methods, results, conclusions)
        key_indicators = [
            r'\b(method|approach|algorithm|technique)\b',
            r'\b(result|finding|performance|accuracy)\b',
            r'\b(conclusion|demonstrate|show|achieve)\b'
        ]
        
        indicators_found = sum(1 for pattern in key_indicators 
                             if re.search(pattern, abstract.lower()))
        score += (indicators_found / len(key_indicators)) * 0.6
        
        return min(score, 1.0)
    
    def _score_author_credibility(self, authors: List[str]) -> float:
        """Score based on author information"""
        if not authors:
            return 0.3  # Neutral score for missing authors
        
        score = 0.5  # Base score
        
        # Prefer papers with multiple authors (collaboration)
        if len(authors) > 1:
            score += 0.2
        
        # Bonus for reasonable number of authors (not too many)
        if 2 <= len(authors) <= 8:
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_category_relevance(self, categories: List[str]) -> float:
        """Score based on category relevance"""
        if not categories:
            return 0.0
        
        relevant_categories = [
            'cs.AI', 'cs.LG', 'cs.IR', 'cs.CV', 'cs.CL', 
            'stat.ML', 'cs.HC', 'cs.DB'
        ]
        
        # Calculate overlap with relevant categories
        relevant_count = sum(1 for cat in categories if cat in relevant_categories)
        
        if relevant_count == 0:
            return 0.2  # Low but not zero for other categories
        
        return min(relevant_count / len(categories), 1.0)
    
    def _score_publication_recency(self, publication_date) -> float:
        """Score based on how recent the publication is"""
        if not publication_date:
            return 0.5  # Neutral score for missing date
        
        try:
            if isinstance(publication_date, str):
                pub_date = datetime.strptime(publication_date, '%Y-%m-%d').date()
            else:
                pub_date = publication_date
            
            days_old = (datetime.utcnow().date() - pub_date).days
            
            # More recent papers get higher scores
            if days_old <= 30:
                return 1.0
            elif days_old <= 90:
                return 0.8
            elif days_old <= 180:
                return 0.6
            elif days_old <= 365:
                return 0.4
            else:
                return 0.2
                
        except Exception:
            return 0.5
    
    async def _enrich_paper_data(
        self, 
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich paper data with additional computed fields"""
        
        enriched_papers = []
        
        for paper in papers:
            enriched_paper = paper.copy()
            
            # Add computed fields
            enriched_paper['word_count'] = self._calculate_word_count(paper)
            enriched_paper['author_count'] = len(paper.get('authors', []))
            enriched_paper['category_count'] = len(paper.get('categories', []))
            enriched_paper['processing_timestamp'] = datetime.utcnow().isoformat()
            
            # Add relevance indicators
            enriched_paper['relevance_indicators'] = await self._extract_relevance_indicators(paper)
            
            # Add content analysis
            enriched_paper['content_analysis'] = await self._analyze_content(paper)
            
            enriched_papers.append(enriched_paper)
        
        return enriched_papers
    
    def _calculate_word_count(self, paper: Dict[str, Any]) -> Dict[str, int]:
        """Calculate word counts for different sections"""
        
        title_words = len((paper.get('title') or '').split())
        abstract_words = len((paper.get('abstract') or '').split())
        
        return {
            'title_words': title_words,
            'abstract_words': abstract_words,
            'total_words': title_words + abstract_words
        }
    
    async def _extract_relevance_indicators(
        self, 
        paper: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract indicators of relevance to e-commerce recommendations"""
        
        text_content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        
        # Define relevance keywords
        relevance_keywords = {
            'recommendation': ['recommend', 'recommendation', 'recommender', 'suggest'],
            'ecommerce': ['ecommerce', 'e-commerce', 'retail', 'shopping', 'purchase', 'buy'],
            'personalization': ['personaliz', 'individual', 'custom', 'tailor'],
            'collaborative_filtering': ['collaborative', 'filtering', 'matrix factorization'],
            'content_based': ['content-based', 'content based', 'item-based'],
            'deep_learning': ['deep learning', 'neural network', 'transformer', 'embedding'],
            'machine_learning': ['machine learning', 'classification', 'clustering', 'regression']
        }
        
        indicators = {}
        for category, keywords in relevance_keywords.items():
            indicators[category] = sum(1 for keyword in keywords if keyword in text_content)
        
        # Calculate overall relevance score
        total_indicators = sum(indicators.values())
        indicators['total_relevance_score'] = total_indicators
        indicators['is_highly_relevant'] = total_indicators >= 3
        
        return indicators
    
    async def _analyze_content(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for additional insights"""
        
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        analysis = {
            'has_methodology': bool(re.search(r'\b(method|approach|algorithm|technique)\b', abstract.lower())),
            'has_evaluation': bool(re.search(r'\b(evaluat|experiment|result|performance)\b', abstract.lower())),
            'has_comparison': bool(re.search(r'\b(compar|baseline|state.of.the.art)\b', abstract.lower())),
            'mentions_dataset': bool(re.search(r'\b(dataset|data set|benchmark|corpus)\b', abstract.lower())),
            'is_survey': bool(re.search(r'\b(survey|review|overview)\b', title.lower())),
            'is_tutorial': bool(re.search(r'\b(tutorial|introduction|primer)\b', title.lower()))
        }
        
        # Count technical depth indicators
        technical_indicators = sum([
            analysis['has_methodology'],
            analysis['has_evaluation'], 
            analysis['has_comparison'],
            analysis['mentions_dataset']
        ])
        
        analysis['technical_depth_score'] = technical_indicators / 4.0
        
        return analysis
    
    async def _standardize_for_storage(
        self, 
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Final standardization before storage"""
        
        standardized_papers = []
        
        for paper in papers:
            standardized = {}
            
            # Core fields
            standardized['paper_id'] = paper['paper_id']
            standardized['title'] = paper['title']
            standardized['abstract'] = paper.get('abstract')
            standardized['authors'] = paper.get('authors', [])
            standardized['publication_date'] = paper.get('publication_date')
            standardized['venue'] = paper.get('venue')
            standardized['arxiv_id'] = paper.get('arxiv_id')
            standardized['semantic_scholar_id'] = paper.get('semantic_scholar_id')
            standardized['categories'] = paper.get('categories', [])
            standardized['full_text'] = paper.get('full_text')
            standardized['created_at'] = datetime.utcnow()
            
            # Quality and processing metadata
            standardized['quality_score'] = paper.get('quality_score', {})
            standardized['word_count'] = paper.get('word_count', {})
            standardized['relevance_indicators'] = paper.get('relevance_indicators', {})
            standardized['content_analysis'] = paper.get('content_analysis', {})
            standardized['processing_timestamp'] = paper.get('processing_timestamp')
            
            # Processing metadata
            standardized['processor_version'] = '1.0'
            standardized['processing_pipeline'] = 'paper_discovery_v1'
            
            standardized_papers.append(standardized)
        
        return standardized_papers

    async def get_processing_statistics(
        self, 
        papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate processing statistics for monitoring"""
        
        if not papers:
            return {}
        
        # Category distribution
        all_categories = []
        for paper in papers:
            all_categories.extend(paper.get('categories', []))
        
        category_counts = Counter(all_categories)
        
        # Quality score distribution
        quality_scores = [
            paper.get('quality_score', {}).get('overall_score', 0) 
            for paper in papers
        ]
        
        # Author count distribution
        author_counts = [len(paper.get('authors', [])) for paper in papers]
        
        # Relevance indicators
        highly_relevant = sum(
            1 for paper in papers 
            if paper.get('relevance_indicators', {}).get('is_highly_relevant', False)
        )
        
        return {
            'total_papers': len(papers),
            'category_distribution': dict(category_counts.most_common(10)),
            'quality_score_stats': {
                'mean': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0
            },
            'author_count_stats': {
                'mean': sum(author_counts) / len(author_counts) if author_counts else 0,
                'min': min(author_counts) if author_counts else 0,
                'max': max(author_counts) if author_counts else 0
            },
            'highly_relevant_papers': highly_relevant,
            'relevance_percentage': (highly_relevant / len(papers)) * 100 if papers else 0
        }
