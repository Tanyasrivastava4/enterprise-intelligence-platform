from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.document import ProcessingStatus

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    content_hash: str
    status: ProcessingStatus
    error_message: Optional[str] = None
    chunk_count: int
    character_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: ProcessingStatus
    message: str
    is_duplicate: bool = False

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_or_row: int
    chunk_index: int
    text: str
    score: Optional[float] = None
