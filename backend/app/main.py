import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.api.auth import router as auth_router
from app.api.election import router as election_router
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.core.websocket import manager

app = FastAPI(
    title="幻想乡委员会选举系统 API",
    description="管理每月最后一天举行的 4 轮淘汰制选举",
    version="1.0.0"
)

# 💡 新增：挂载本地上传目录，使得图片可以通过 URL 直接访问
os.makedirs("uploads/avatars", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 允许跨域请求（方便前端 8004 端口调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议改为 ["http://localhost:8004", "您的服务器IP:8004"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["权限认证"])
app.include_router(election_router, prefix="/api/election", tags=["选举核心业务"])
app.include_router(admin_router, prefix="/api/admin", tags=["管理员专属"])
app.include_router(chat_router, prefix="/api/chat", tags=["聊天大厅"])

@app.get("/")
async def root():
    return {"message": "幻想乡委员会选举系统后端已启动！", "status": "running"}

@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # 尝试执行一个最简单的 SQL 查询来验证连接
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {"status": "ok", "db_connected": True, "test_query": value}
    except Exception as e:
        return {"status": "error", "db_connected": False, "error_detail": str(e)}

@app.websocket("/ws/election")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 在这个业务场景下，前端主要是接收广播，很少通过 WS 发消息给后端。
            # 但为了保持连接活跃，我们可以接收前端发来的心跳包 (ping)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)