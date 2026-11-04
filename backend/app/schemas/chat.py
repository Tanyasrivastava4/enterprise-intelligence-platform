from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class Citation(BaseModel):
    document_id: str
    document_name: str
    page_or_row: int
    chunk_id: str
    excerpt: str
    similarity_score: float

class ChatQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None  # Optional metadata filter
    model_override: Optional[str] = None
    temperature: float = 0.2
    hybrid_search: bool = True

class ChatQueryResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: List[Citation]
    conflicts_detected: List[str] = []
    is_grounded: bool = True
    model_used: str
    provider_used: str
    is_fallback: bool
    tokens_prompt: int
    tokens_completion: int
    total_tokens: int
    latency_ms: int
    created_at: datetime
