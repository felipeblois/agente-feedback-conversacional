from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    actor: str
    source: str
    expires_at: datetime


class AdminSessionResponse(BaseModel):
    authenticated: bool
    actor: str
    source: str
    expires_at: datetime


class AdminUserCreateRequest(BaseModel):
    username: str
    full_name: str = ""
    password: str


class AdminUserUpdateRequest(BaseModel):
    full_name: str = ""
    is_active: bool = True


class AdminPasswordUpdateRequest(BaseModel):
    password: str


class AdminUserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
