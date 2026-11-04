from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="New Enterprise Session")
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)  # For long-context summarization
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # RAG & Agent Metadata
    citations: Mapped[dict] = mapped_column(JSON, nullable=True)  # List of chunk citations [doc_id, page, excerpt]
    agent_trace: Mapped[dict] = mapped_column(JSON, nullable=True) # Tool calls, parameters, intermediate outputs
    model_used: Mapped[str] = mapped_column(String(100), nullable=True)
    provider_used: Mapped[str] = mapped_column(String(50), nullable=True)
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    is_fallback: Mapped[bool] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
