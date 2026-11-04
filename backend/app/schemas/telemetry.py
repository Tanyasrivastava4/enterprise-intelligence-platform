from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel

class TelemetrySummary(BaseModel):
    total_queries: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    fallback_count: int
    error_count: int
    active_documents: int

class TelemetryLogItem(BaseModel):
    id: str
    endpoint: str
    query: Optional[str]
    provider: str
    model: str
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    fallback_triggered: bool
    status_code: int
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
