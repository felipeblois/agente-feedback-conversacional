from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    title: str
    description: Optional[str] = None
    score_type: str = "treinamento"
    theme_summary: Optional[str] = None
    session_goal: Optional[str] = None
    target_audience: Optional[str] = None
    topics_to_explore: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_anonymous: bool = True
    max_followup_questions: int = 3
    public_link_enabled: bool = True
    public_link_expires_at: Optional[datetime] = None
    status: str = "active"


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    score_type: Optional[str] = None
    theme_summary: Optional[str] = None
    session_goal: Optional[str] = None
    target_audience: Optional[str] = None
    topics_to_explore: Optional[str] = None
    ai_guidance: Optional[str] = None
    is_anonymous: Optional[bool] = None
    max_followup_questions: Optional[int] = None
    public_link_enabled: Optional[bool] = None
    public_link_expires_at: Optional[datetime] = None
    status: Optional[str] = None


class SessionResponse(SessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_token: str
    created_by_admin_username: Optional[str] = None
    updated_by_admin_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(SessionResponse):
    response_count: int = 0
    completed_response_count: int = 0
    completion_rate: float = 0.0
    avg_score: Optional[float] = None
    analysis_count: int = 0
    last_analysis_at: Optional[datetime] = None


class DashboardSummaryResponse(BaseModel):
    total_sessions: int
    total_responses: int
    average_completion_rate: float
    average_score: Optional[float] = None
    analyses_completed: int
    last_analysis_at: Optional[datetime] = None
    active_sessions: int
    archived_sessions: int
    completed_responses: int
    sessions_with_analysis: int
    completion_leader_title: Optional[str] = None
    response_leader_title: Optional[str] = None
    score_leader_title: Optional[str] = None
    executive_highlights: List[str] = []
    recent_sessions: List[SessionListResponse]


class ScoreDistributionItem(BaseModel):
    score: int
    count: int


class RecentResponseItem(BaseModel):
    response_id: int
    participant_label: str
    score: Optional[int] = None
    status: str
    latest_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class SessionDetailResponse(SessionListResponse):
    latest_analysis_summary: Optional[str] = None
    public_url: str
    public_link_status: str
    score_distribution: List[ScoreDistributionItem]
    recent_responses: List[RecentResponseItem]
