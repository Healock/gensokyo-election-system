from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.websocket import manager
from app.core.database import get_db
from app.models.models import Member, Election, Round, Vote
from app.api.deps import get_current_user, get_admin_user

import math

router = APIRouter()

@router.get("/current")
async def get_current_election_info(db: AsyncSession = Depends(get_db)):
    """获取当前选举状态、动态候选人名单与大结局"""
    result = await db.execute(select(Election).where(Election.status.in_(['active', 'completed'])).order_by(Election.created_at.desc()))
    election = result.scalars().first()
    
    if not election:
        return {"status": "idle", "message": "当前非选举期"}
        
    # 💡 新增：提取选举的开启时间，供前端时钟计算进度
    start_time_str = election.created_at.isoformat() if election.created_at else None
        
    if election.status == 'completed':
        winner_res = await db.execute(select(Member).where(Member.id == election.winner_id))
        winner = winner_res.scalars().first()
        
        final_round_res = await db.execute(select(Round).where(and_(Round.election_id == election.id, Round.round_number == 4)))
        final_round = final_round_res.scalars().first()
        tally = []
        if final_round:
            stmt = select(Vote.candidate_id, Member.username, func.count(Vote.id).label('vote_count')) \
                .join(Member, Vote.candidate_id == Member.id) \
                .where(and_(Vote.round_id == final_round.id, Vote.candidate_id.isnot(None))) \
                .group_by(Vote.candidate_id, Member.username).order_by(desc('vote_count'))
            tally_res = await db.execute(stmt)
            tally = [{"candidate_id": str(r.candidate_id), "username": r.username, "vote_count": r.vote_count} for r in tally_res.all()]

        return {
            "status": "completed",
            "start_time": start_time_str,  # 👈 传给前端
            "winner": {"id": str(winner.id), "username": winner.username} if winner else None,
            "final_tally": tally
        }

    result = await db.execute(select(Round).where(and_(Round.election_id == election.id, Round.status == 'voting')))
    current_round = result.scalars().first()
    if not current_round:
        return {"status": "tallying", "start_time": start_time_str, "message": "绝赞计票中..."}

    round_num = current_round.round_number
    prev_tally = []
    eliminated = []
    
    if round_num == 1:
        res = await db.execute(select(Member).where(and_(Member.is_current_chairman == False, Member.is_admin == False)))
        candidates = [{"id": str(m.id), "username": m.username} for m in res.scalars().all()]
    else:
        prev_round_res = await db.execute(select(Round).where(and_(Round.election_id == election.id, Round.round_number == round_num - 1)))
        prev_round = prev_round_res.scalars().first()
        
        stmt = select(Vote.candidate_id, Member.username, func.count(Vote.id).label('vote_count')) \
            .join(Member, Vote.candidate_id == Member.id) \
            .where(and_(Vote.round_id == prev_round.id, Vote.candidate_id.isnot(None))) \
            .group_by(Vote.candidate_id, Member.username).order_by(desc('vote_count'))
        tally_res = await db.execute(stmt)
        full_tally = [{"id": str(r.candidate_id), "username": r.username, "vote_count": r.vote_count} for r in tally_res.all()]
        
        total_candidates = len(full_tally)
        keep_count = total_candidates
        
        if round_num == 2: keep_count = math.ceil(total_candidates * 0.5)
        elif round_num == 3: keep_count = 2
            
        if keep_count > 0 and keep_count < total_candidates:
            cutoff_votes = full_tally[keep_count - 1]["vote_count"]
            candidates = [c for c in full_tally if c["vote_count"] >= cutoff_votes]
            eliminated = [c for c in full_tally if c["vote_count"] < cutoff_votes]
        else:
            candidates = full_tally
            eliminated = []
            
        prev_tally = full_tally

    return {
        "status": "voting",
        "start_time": start_time_str, # 👈 传给前端
        "round_number": round_num,
        "candidates": candidates,
        "prev_tally": prev_tally,
        "eliminated": eliminated
    }

# 接收投票的请求体 (候选人ID为空则代表弃权)
class VoteRequest(BaseModel):
    candidate_id: Optional[UUID] = None

@router.post("/vote")
async def submit_vote(
    vote_req: VoteRequest, 
    current_user: Member = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """提交选票接口"""
    # 1. 查找当前活跃的选举和正在投票中的轮次
    if current_user.is_admin:
        raise HTTPException(status_code=403, detail="管理员为中立观察者，不参与投票")
    result = await db.execute(select(Election).where(Election.status == 'active'))
    election = result.scalars().first()
    if not election:
        raise HTTPException(status_code=400, detail="当前没有正在进行的选举")
        
    result = await db.execute(
        select(Round).where(and_(Round.election_id == election.id, Round.status == 'voting'))
    )
    current_round = result.scalars().first()
    if not current_round:
        raise HTTPException(status_code=400, detail="当前不在法定投票时间段内")
        
    # 2. 利益回避原则：绝对不能投给自己
    if vote_req.candidate_id and str(vote_req.candidate_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="利益回避：不能将票投予本人")
        
    # 3. 防刷票：检查本轮是否已经投过
    existing_vote = await db.execute(
        select(Vote).where(and_(Vote.round_id == current_round.id, Vote.voter_id == current_user.id))
    )
    if existing_vote.scalars().first():
        raise HTTPException(status_code=400, detail="您在本轮次已完成投票，不可重复提交")
        
    # 4. 写入选票
    new_vote = Vote(
        election_id=election.id,
        round_id=current_round.id,
        voter_id=current_user.id,
        candidate_id=vote_req.candidate_id
    )
    db.add(new_vote)
    await db.commit()
    
    return {"message": "投票成功！", "round": current_round.round_number}

# ----------------- 测试专用接口 -----------------
@router.post("/debug/start_election")
async def debug_start_election(admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """[开发专用] 手动强制开启一场选举并进入第一轮投票"""
    # 生成当前年月字符串，例如 2026-03
    current_ym = datetime.now().strftime("%Y-%m")
    
    # 清理掉可能存在的同月测试数据
    old_elections = await db.execute(select(Election).where(Election.year_month == current_ym))
    for old_e in old_elections.scalars().all():
        await db.delete(old_e)
    await db.commit()

    # 创建一场新选举
    new_election = Election(year_month=current_ym, status='active')
    db.add(new_election)
    await db.commit()
    await db.refresh(new_election)
    
    # 自动开启第一轮
    first_round = Round(election_id=new_election.id, round_number=1, status='voting')
    db.add(first_round)
    await db.commit()
    
    # 📢 触发 WebSocket 广播：选举开启
    await manager.broadcast({"event": "election_started", "round": 1})
    
    return {"message": f"成功开启 {current_ym} 选举，第一轮投票已解锁！"}
    
@router.post("/debug/tally_round")
async def debug_tally_round(admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """[开发专用] 结算当前轮次，输出晋级名单并自动推进到下一轮"""
    
    # 1. 找到当前正在投票的轮次
    result = await db.execute(select(Election).where(Election.status == 'active'))
    election = result.scalars().first()
    if not election:
        raise HTTPException(status_code=400, detail="没有正在进行的选举")
        
    result = await db.execute(
        select(Round).where(and_(Round.election_id == election.id, Round.status == 'voting'))
    )
    current_round = result.scalars().first()
    if not current_round:
        raise HTTPException(status_code=400, detail="当前没有正在投票的轮次")

    # 2. 统计票数
    stmt = select(
        Vote.candidate_id, 
        func.count(Vote.id).label('vote_count')
    ).where(
        and_(Vote.round_id == current_round.id, Vote.candidate_id.isnot(None))
    ).group_by(Vote.candidate_id).order_by(desc('vote_count'))
    
    votes_result = await db.execute(stmt)
    rows = votes_result.all() 
    
    # 核心修复：把 SQLAlchemy 的 Row 对象强制转换为标准字典，并将 UUID 转为字符串
    tally = [{"candidate_id": str(row.candidate_id), "vote_count": row.vote_count} for row in rows]
    
    total_candidates_with_votes = len(tally)
    if total_candidates_with_votes == 0:
        return {"message": "本轮没有任何有效投票（全员弃权或未投票）", "round": current_round.round_number}

    advanced_candidates = []
    round_num = current_round.round_number

    # 3. 严格执行《章程》的淘汰算法与【平票保护机制】！
    if round_num in [1, 2, 3]:
        keep_count = total_candidates_with_votes
        if round_num in [1, 2]:
            keep_count = math.ceil(total_candidates_with_votes * 0.5)
        elif round_num == 3:
            keep_count = 2
            
        if keep_count > 0 and keep_count < total_candidates_with_votes:
            # 💡 神仙逻辑：找到及格线票数，所有达到及格线的人并列晋级！
            cutoff_votes = tally[keep_count - 1]["vote_count"]
            advanced_candidates = [c for c in tally if c["vote_count"] >= cutoff_votes]
        else:
            # 投票人数过少，直接全员保留
            advanced_candidates = tally
            
    elif round_num == 4:
        # 第四轮决选：票高者胜出
        if total_candidates_with_votes >= 2 and tally[0]["vote_count"] == tally[1]["vote_count"]:
            return {"message": "出现平票！触发现任委员长裁决机制！", "tally": tally}
        else:
            winner_id = tally[0]["candidate_id"]
            election.winner_id = winner_id
            election.status = 'completed'
            current_round.status = 'finished'
            await db.commit()
            
            # 📢 触发 WebSocket 广播：大结局，新委员长诞生
            await manager.broadcast({
                "event": "election_completed", 
                "winner_id": winner_id, 
                "final_tally": tally
            })
            
            return {"message": "选举结束！新任委员长已诞生！", "winner_id": winner_id, "final_tally": tally}

    # 4. 结算当前轮次，开启下一轮
    current_round.status = 'finished'
    
    new_round = Round(
        election_id=election.id,
        round_number=round_num + 1,
        status='voting'
    )
    db.add(new_round)
    await db.commit()
    
    # 📢 触发 WebSocket 广播：进入下一轮
    await manager.broadcast({
        "event": "round_advanced", 
        "new_round": round_num + 1,
        "tally_result": tally,
        "advanced_candidates": [c["candidate_id"] for c in advanced_candidates]
    })
    
    return {
        "message": f"第 {round_num} 轮计票完成！第 {round_num + 1} 轮已开启。",
        "tally_result": tally,
        "advanced_candidates": [c["candidate_id"] for c in advanced_candidates]
    }
    
# ========== 新增的两个接口 ==========

@router.get("/history")
async def get_election_history(db: AsyncSession = Depends(get_db)):
    """获取所有历史选举结果"""
    stmt = select(Election.year_month, Member.username.label('winner_name')) \
        .outerjoin(Member, Election.winner_id == Member.id) \
        .where(Election.status.in_(['completed', 'archived'])) \
        .order_by(desc(Election.year_month))
    res = await db.execute(stmt)
    return [{"year_month": r.year_month, "winner": r.winner_name or "流局"} for r in res.all()]

@router.post("/debug/archive")
async def admin_archive_election(admin: Member = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """管理员手动关闭大结局展示页"""
    res = await db.execute(select(Election).where(Election.status == 'completed'))
    election = res.scalars().first()
    if election:
        election.status = 'archived'
        await db.commit()
        await manager.broadcast({"event": "archived"}) # 通知全服刷新页面
    return {"message": "大结局页面已归档隐藏"}