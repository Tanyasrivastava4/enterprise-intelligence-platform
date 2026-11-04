from datetime import datetime, timezone
import uuid
import enum
from sqlalchemy import String, Integer, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, txt, md, csv
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False) # SHA-256 for duplicate detection
    
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    character_count: Mapped[int] = mapped_column(Integer, default=0)
    
    uploader_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    uploader = relationship("User", back_populates="documents")
