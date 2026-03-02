-- 幻想乡委员会选举系统 - 终极 Schema (2026-03 版)
-- 包含：头像支持、注册审核、管理员标记、级联删除

-- 1. 委员表 (Members)
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,      
    password_hash VARCHAR(255) NOT NULL,       
    avatar_url TEXT,                           -- 👈 新增：本地压缩头像路径或网络链接
    is_current_chairman BOOLEAN DEFAULT FALSE, 
    is_admin BOOLEAN DEFAULT FALSE,            -- 👈 管理员标记
    is_approved BOOLEAN DEFAULT FALSE,         -- 👈 注册审核标记
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 选举总表 (Elections)
CREATE TABLE elections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year_month VARCHAR(10) UNIQUE NOT NULL,    -- 例：'2026-03'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, active, completed, archived
    winner_id UUID REFERENCES members(id) ON DELETE SET NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 轮次状态表 (Rounds)
CREATE TABLE rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    round_number INT NOT NULL,                 -- 1, 2, 3, 4
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- voting, tallying, finished
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(election_id, round_number)          
);

-- 4. 投票记录表 (Votes)
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
    voter_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE, -- 委员除名则选票作废
    candidate_id UUID REFERENCES members(id) ON DELETE CASCADE, -- 候选人除名则该票失效
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(round_id, voter_id)                 
);

-- 5. 性能优化索引
CREATE INDEX idx_votes_round ON votes(round_id);
CREATE INDEX idx_votes_election ON votes(election_id);