from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    fallback_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
