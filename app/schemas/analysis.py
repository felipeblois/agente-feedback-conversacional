from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AnalysisRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    top_positive_themes: List[str]
    top_negative_themes: List[str]
    avg_score: Optional[float]
    response_count: int
    positives: List[str] = []
    negatives: List[str] = []
    recommendations: List[str] = []
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: Optional[datetime] = None
