class Settings:
    # ... existing settings ...
    
    # Paper processing settings
    MIN_QUALITY_SCORE: float = float(os.getenv("MIN_QUALITY_SCORE", "0.4"))
    RELEVANT_CATEGORIES: List[str] = [
        "cs.AI", "cs.LG", "cs.IR", "cs.CV", "cs.CL", 
        "stat.ML", "cs.HC", "cs.DB"
    ]
    
    # Quality thresholds
    MIN_TITLE_LENGTH: int = 10
    MAX_TITLE_LENGTH: int = 500
    MIN_ABSTRACT_LENGTH: int = 100
    MAX_ABSTRACT_LENGTH: int = 10000
