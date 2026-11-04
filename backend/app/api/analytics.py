from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.telemetry import TelemetryLog
from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.api.auth import get_current_user
from app.schemas.telemetry import TelemetrySummary, TelemetryLogItem

router = APIRouter(prefix="/analytics", tags=["Observability & Analytics"])

@router.get("/summary", response_model=TelemetrySummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates overall usage metrics: queries, tokens, costs, average latency, and fallback events."""
    # Total queries count
    count_stmt = select(func.count(TelemetryLog.id))
    total_queries = (await db.execute(count_stmt)).scalar() or 0

    # Total tokens
    tokens_stmt = select(func.sum(TelemetryLog.total_tokens))
    total_tokens = (await db.execute(tokens_stmt)).scalar() or 0

    # Total estimated cost
    cost_stmt = select(func.sum(TelemetryLog.estimated_cost_usd))
    total_cost = (await db.execute(cost_stmt)).scalar() or 0.0

    # Average latency
    lat_stmt = select(func.avg(TelemetryLog.latency_ms))
    avg_lat = (await db.execute(lat_stmt)).scalar() or 0.0

    # Fallback count
    fb_stmt = select(func.count(TelemetryLog.id)).where(TelemetryLog.fallback_triggered == True)
    fallback_count = (await db.execute(fb_stmt)).scalar() or 0

    # Error count
    err_stmt = select(func.count(TelemetryLog.id)).where(TelemetryLog.status_code >= 400)
    error_count = (await db.execute(err_stmt)).scalar() or 0

    # Active documents
    doc_stmt = select(func.count(Document.id)).where(Document.status == ProcessingStatus.INDEXED)
    active_docs = (await db.execute(doc_stmt)).scalar() or 0

    return TelemetrySummary(
        total_queries=total_queries,
        total_tokens=int(total_tokens),
        total_cost_usd=round(float(total_cost), 4),
        avg_latency_ms=round(float(avg_lat), 1),
        fallback_count=fallback_count,
        error_count=error_count,
        active_documents=active_docs
    )

@router.get("/logs", response_model=List[TelemetryLogItem])
async def get_recent_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches recent query logs and telemetry items."""
    stmt = select(TelemetryLog).order_by(TelemetryLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [TelemetryLogItem.model_validate(l) for l in logs]
