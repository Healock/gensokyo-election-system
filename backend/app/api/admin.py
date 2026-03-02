from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Member
from app.schemas.schemas import MemberCreate, MemberResponse
from app.core.security import get_password_hash
from app.api.deps import get_admin_user

router = APIRouter()

# 接收修改密码的请求体
class PasswordReset(BaseModel):
    new_password: str

@router.get("/users", response_model=list[MemberResponse])
async def get_all_users(admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """获取全员名单"""
    result = await db.execute(select(Member).order_by(Member.created_at.desc()))
    return result.scalars().all()

@router.post("/users", response_model=MemberResponse)
async def create_user_by_admin(user_in: MemberCreate, admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """管理员手动添加委员"""
    result = await db.execute(select(Member).where(Member.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="该账号已存在，请换一个名称")
    
    new_member = Member(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member

@router.delete("/users/{user_id}")
async def delete_user(user_id: UUID, admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """管理员删除委员"""
    result = await db.execute(select(Member).where(Member.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="系统保护：禁止删除最高管理员")
    
    await db.delete(user)
    await db.commit()
    return {"message": f"委员 {user.username} 已被永久除名"}

@router.put("/users/{user_id}/password")
async def reset_password(user_id: UUID, payload: PasswordReset, admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """管理员重置委员密码"""
    result = await db.execute(select(Member).where(Member.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": f"委员 {user.username} 的密码已重置"}
    
@router.put("/users/{user_id}/approve")
async def approve_user(user_id: UUID, admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """管理员批准新委员"""
    result = await db.execute(select(Member).where(Member.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.is_approved = True
    await db.commit()
    return {"message": f"已正式批准 {user.username} 加入委员会！"}