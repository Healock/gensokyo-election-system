from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

# 基础模型
class MemberBase(BaseModel):
    username: str

# 注册/登录时接收的数据结构（账号+密码）
class MemberCreate(MemberBase):
    password: str

# 返回给前端的用户信息（滤掉了密码哈希值，非常安全）
class MemberResponse(BaseModel):
    id: UUID
    username: str
    is_current_chairman: bool
    is_admin: bool
    is_approved: bool
    avatar_url: str | None = None  # 👈 新增这一行
    created_at: datetime

    class Config:
        from_attributes = True

# Token 结构
class Token(BaseModel):
    access_token: str
    token_type: str