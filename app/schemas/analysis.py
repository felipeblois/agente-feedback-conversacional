from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalysisRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None

class AnalysisResponse(BaseModel):
    summary: str
    top_positive_themes: List[str]
    top_negative_themes: List[str]
    avg_score: Optional[float]
    response_count: int
    
    class Config:
        from_attributes = True
