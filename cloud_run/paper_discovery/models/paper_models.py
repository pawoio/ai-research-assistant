# Add these to your existing paper_models.py

from pydantic import BaseModel
from typing import Dict, Any, Optional

class QualityScore(BaseModel):
    """Quality assessment scores for a paper"""
    title_score: float = Field(ge=0.0, le=1.0)
    abstract_score: float = Field(ge=0.0, le=1.0)
    author_score: float = Field(ge=0.0, le=1.0)
    category_score: float = Field(ge=0.0, le=1.0)
    recency_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

class ProcessedPaper(PaperData):
    """Extended paper model with processing metadata"""
    quality_score: Optional[QualityScore] = None
    word_count: Optional[Dict[str, int]] = None
    relevance_indicators: Optional[Dict[str, Any]] = None
    content_analysis: Optional[Dict[str, Any]] = None
    processing_timestamp: Optional[str] = None
    processor_version: Optional[str] = None
    processing_pipeline: Optional[str] = None

class ProcessingStats(BaseModel):
    """Statistics from paper processing"""
    processing_time_seconds: float
    input_papers: int
    validated_papers: int
    deduplicated_papers: int
    quality_filtered_papers: int
    final_papers: int
    duplicates_removed: int
    quality_filtered_out: int
    enriched_count: int
    processing_timestamp: str
