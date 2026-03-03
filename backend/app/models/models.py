import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, UniqueConstraint, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Member(Base):
    __tablename__ = 'members'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_current_chairman = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    avatar_url = Column(Text, nullable=True) 

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Election(Base):
    __tablename__ = 'elections'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year_month = Column(String(10), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    winner_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Round(Base):
    __tablename__ = 'rounds'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey('elections.id', ondelete='CASCADE'), nullable=False)
    round_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint('election_id', 'round_number', name='uq_election_round'),)

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey('elections.id', ondelete='CASCADE'), nullable=False)
    round_id = Column(UUID(as_uuid=True), ForeignKey('rounds.id', ondelete='CASCADE'), nullable=False)
    voter_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint('round_id', 'voter_id', name='uq_round_voter'),)
    
class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender = relationship("Member")