from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.websocket import manager
from app.core.image_utils import compress_and_save_image
from app.models.models import Member, Vote, Round, Election
from app.schemas.schemas import MemberCreate, Token, MemberResponse
from app.api.deps import get_current_user

router = APIRouter()

# ==========================================
# Pydantic 接收模型
# ==========================================
class AvatarUpdate(BaseModel):
    avatar_url: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# ==========================================
# 路由接口
# ==========================================

@router.post("/register", response_model=MemberResponse)
async def register_member(user_in: MemberCreate, db: AsyncSession = Depends(get_db)):
    """新委员自行注册（默认未审批）"""
    result = await db.execute(select(Member).where(Member.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="该委员代号已被占用！")
    
    new_member = Member(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        is_approved=False
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    await manager.broadcast({"event": "user_list_updated"})
    
    return new_member

@router.post("/login", response_model=Token)
async def login(form_data: MemberCreate, db: AsyncSession = Depends(get_db)):
    """委员登录"""
    result = await db.execute(select(Member).where(Member.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="代号或密码错误")
        
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="入会申请已提交，正等待最高委员会审批...")
        
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_current_user_info(current_user: Member = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "is_approved": current_user.is_approved,
        "avatar_url": current_user.avatar_url
    }

@router.put("/me/avatar")
async def update_my_avatar(payload: AvatarUpdate, current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """个人中心：更新头像"""
    current_user.avatar_url = payload.avatar_url
    await db.commit()
    return {"message": "头像已更新", "avatar_url": current_user.avatar_url}

@router.put("/me/password")
async def update_my_password(payload: PasswordChange, current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """个人中心：修改密码"""
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误！")
    
    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "密码修改成功！请牢记新密码。"}

@router.get("/me/votes")
async def get_my_vote_history(current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """个人中心：查询自己的投票历史"""
    # 联合查询：选票 -> 轮次 -> 选举 -> 候选人
    stmt = select(Vote, Round, Election, Member.username.label("candidate_name")) \
        .join(Round, Vote.round_id == Round.id) \
        .join(Election, Round.election_id == Election.id) \
        .outerjoin(Member, Vote.candidate_id == Member.id) \
        .where(Vote.voter_id == current_user.id) \
        .order_by(Election.created_at.desc(), Round.round_number.desc())
        
    res = await db.execute(stmt)
    rows = res.all()
    
    history = []
    for vote, rnd, elec, c_name in rows:
        history.append({
            "election_ym": elec.year_month,
            "round_num": rnd.round_number,
            "candidate_name": c_name or "弃权",
            "vote_time": vote.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return history
    
from app.core.image_utils import compress_and_save_image

@router.post("/me/avatar/upload")
async def upload_my_avatar(file: UploadFile = File(...), current_user: Member = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """个人中心：接收本地图片，压缩并保存"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件！")
        
    file_bytes = await file.read()
    file_url = compress_and_save_image(file_bytes, file.filename)
    
    current_user.avatar_url = file_url
    await db.commit()
    return {"message": "头像上传成功！", "avatar_url": file_url}