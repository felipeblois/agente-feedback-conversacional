from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RetentionPolicyResponse(BaseModel):
    responses_days: int
    analyses_days: int
    logs_days: int
    exports_days: int
    legal_basis_label: str
    ai_disclaimer: str
    privacy_contact_email: Optional[str] = None


class SessionPrivacySummaryResponse(BaseModel):
    session_id: int
    session_title: str
    total_participants: int
    identified_participants: int
    anonymous_participants: int
    total_responses: int
    completed_responses: int
    analysis_runs: int
    export_files: int
    retention_policy: RetentionPolicyResponse
    session_delete_scope: str
    participant_anonymization_scope: str


class ParticipantMessageExport(BaseModel):
    message_id: int
    sender: str
    message_type: str
    message_text: str
    created_at: datetime


class ParticipantResponseExport(BaseModel):
    response_id: int
    status: str
    score: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    messages: List[ParticipantMessageExport]


class ParticipantDataExportResponse(BaseModel):
    session_id: int
    participant_id: int
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    anonymous: bool
    created_at: datetime
    responses: List[ParticipantResponseExport]


class ParticipantAnonymizeResponse(BaseModel):
    session_id: int
    participant_id: int
    anonymous: bool
    removed_identifiers: bool
    response_count: int
