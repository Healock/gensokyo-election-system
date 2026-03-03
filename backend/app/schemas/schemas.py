from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MemberBase(BaseModel):
    username: str

class MemberCreate(MemberBase):
    password: str

class MemberResponse(BaseModel):
    id: UUID
    username: str
    is_current_chairman: bool
    is_admin: bool
    is_approved: bool
    avatar_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str