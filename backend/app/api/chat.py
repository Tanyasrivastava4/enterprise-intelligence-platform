from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.api.auth import get_current_user
from app.services.retrieval.rag_engine import rag_engine
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse, Citation

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])

@router.post("/query", response_model=ChatQueryResponse)
async def query_knowledge_base(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Answers user queries with hybrid retrieval, citations, and multi-model fallback."""
    # 1. Manage Conversation Session
    conv_id = payload.conversation_id
    if not conv_id:
        conversation = Conversation(
            title=payload.query[:60] + "...",
            user_id=current_user.id if current_user else None
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conv_id = conversation.id
    else:
        stmt = select(Conversation).where(Conversation.id == conv_id)
        res = await db.execute(stmt)
        conversation = res.scalar_one_or_none()
        if not conversation:
            conversation = Conversation(id=conv_id, title=payload.query[:60], user_id=current_user.id if current_user else None)
            db.add(conversation)
            await db.commit()

    # 2. Fetch recent conversation history (sliding window for context management)
    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .limit(6)
    )
    msg_res = await db.execute(msg_stmt)
    recent_messages = list(reversed(msg_res.scalars().all()))

    history = [{"role": m.role, "content": m.content} for m in recent_messages]

    # 3. Save User Message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=payload.query
    )
    db.add(user_msg)
    await db.commit()

    # 4. Execute RAG Query
    rag_result = await rag_engine.execute_query(
        query=payload.query,
        conversation_history=history,
        document_ids=payload.document_ids,
        use_hybrid=payload.hybrid_search,
        preferred_provider=payload.model_override,
        db=db
    )

    # 5. Save Assistant Message with Citations & Metadata
    asst_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=rag_result["answer"],
        citations=rag_result["citations"],
        model_used=rag_result["model_used"],
        provider_used=rag_result["provider_used"],
        tokens_prompt=rag_result["tokens_prompt"],
        tokens_completion=rag_result["tokens_completion"],
        latency_ms=rag_result["latency_ms"],
        is_fallback=rag_result["is_fallback"]
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    citations_list = [Citation(**c) for c in rag_result["citations"]]

    return ChatQueryResponse(
        conversation_id=conv_id,
        message_id=asst_msg.id,
        answer=rag_result["answer"],
        citations=citations_list,
        conflicts_detected=rag_result.get("conflicts_detected", []),
        is_grounded=rag_result.get("is_grounded", True),
        model_used=rag_result["model_used"],
        provider_used=rag_result["provider_used"],
        is_fallback=rag_result["is_fallback"],
        tokens_prompt=rag_result["tokens_prompt"],
        tokens_completion=rag_result["tokens_completion"],
        total_tokens=rag_result["total_tokens"],
        latency_ms=rag_result["latency_ms"],
        created_at=asst_msg.created_at
    )

@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists conversations for user."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id if current_user else True)
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    convs = res.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        for c in convs
    ]

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches full message history with citations and execution traces for a conversation."""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    res = await db.execute(stmt)
    msgs = res.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "agent_trace": m.agent_trace,
            "model_used": m.model_used,
            "provider_used": m.provider_used,
            "is_fallback": m.is_fallback,
            "latency_ms": m.latency_ms,
            "created_at": m.created_at
        }
        for m in msgs
    ]
