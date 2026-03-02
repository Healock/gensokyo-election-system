from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_db
from app.models.models import ChatMessage, Member
from app.api.deps import get_current_user
from app.core.websocket import manager
from app.api.deps import get_admin_user

router = APIRouter()

class ChatSend(BaseModel):
    content: str

@router.get("/history")
async def get_chat_history(limit: int = 50, db: AsyncSession = Depends(get_db), current_user: Member = Depends(get_current_user)):
    """获取最近的聊天记录"""
    # 联表查出发件人信息
    stmt = select(ChatMessage).options(selectinload(ChatMessage.sender)).order_by(desc(ChatMessage.created_at)).limit(limit)
    res = await db.execute(stmt)
    messages = res.scalars().all()
    
    # 倒序返回，让前端按时间正序排列（旧的在上，新的在下）
    return [{
        "id": str(m.id),
        "sender_name": m.sender.username,
        "sender_avatar": m.sender.avatar_url,
        "is_admin": m.sender.is_admin,
        "content": m.content,
        "created_at": m.created_at.isoformat()
    } for m in reversed(messages)]

@router.post("/send")
async def send_chat_message(payload: ChatSend, db: AsyncSession = Depends(get_db), current_user: Member = Depends(get_current_user)):
    """发送消息并触发全服广播"""
    new_msg = ChatMessage(sender_id=current_user.id, content=payload.content)
    db.add(new_msg)
    await db.commit()
    
    # 💡 核心：通过 WebSocket 将消息瞬间广播给全服所有人！
    await manager.broadcast({
        "event": "chat_message",
        "message": {
            "id": str(new_msg.id),
            "sender_name": current_user.username,
            "sender_avatar": current_user.avatar_url,
            "is_admin": current_user.is_admin,
            "content": payload.content,
            "created_at": new_msg.created_at.isoformat()
        }
    })
    return {"status": "ok"}
    
@router.delete("/{message_id}")
async def delete_chat_message(message_id: UUID, db: AsyncSession = Depends(get_db), admin: Member = Depends(get_admin_user)):
    """管理员删除聊天记录"""
    res = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    msg = res.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    await db.delete(msg)
    await db.commit()
    
    # 💡 广播“删除事件”，让所有人屏幕上的这条消息瞬间消失
    await manager.broadcast({
        "event": "chat_message_deleted",
        "message_id": str(message_id)
    })
    return {"status": "ok"}