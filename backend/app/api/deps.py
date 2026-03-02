from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.models import Member

# 💡 魔法在这里：启用 FastAPI 内置的 Bearer Token 拦截器
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
) -> Member:
    """
    解析 Token 并返回当前登录的委员。
    使用了 HTTPBearer 后，Swagger UI 会自动出现 🔒 Authorize 按钮。
    """
    # HTTPBearer 会自动帮我们剥离掉 "Bearer " 前缀，直接拿到纯 Token
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的 Token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token 已过期或不合法")
    
    result = await db.execute(select(Member).where(Member.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user
    
async def get_admin_user(current_user: Member = Depends(get_current_user)) -> Member:
    """权限校验：必须是管理员才能放行"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="越权操作：需要最高管理员权限！")
    return current_user