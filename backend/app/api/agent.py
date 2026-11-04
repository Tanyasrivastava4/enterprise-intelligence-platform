from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.telemetry import TelemetryLog
from app.api.auth import get_current_user
from app.services.agent.agent_runner import agent_runner
from app.schemas.agent import AgentTaskRequest, AgentTaskResponse

router = APIRouter(prefix="/agent", tags=["Autonomous Agent"])

@router.post("/run", response_model=AgentTaskResponse)
async def run_agent_task(
    payload: AgentTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes multi-step autonomous agent workflow across Knowledge Base Search,

    Document Analysis, and Structured Report Generation.
    """
    conv_id = payload.conversation_id
    if not conv_id:
        conv = Conversation(
            title=f"Agent: {payload.task[:50]}...",
            user_id=current_user.id if current_user else None
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # 1. Save user task message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=f"[AGENT GOAL]: {payload.task}"
    )
    db.add(user_msg)
    await db.commit()

    # 2. Run Autonomous Agent Loop
    agent_response = await agent_runner.execute_task(
        task=payload.task,
        conversation_id=conv_id,
        max_steps=payload.max_steps
    )

    # 3. Format Agent Trace for Database Storage
    trace_data = [step.model_dump() for step in agent_response.steps]

    # 4. Save Assistant Response with Agent Execution Trace
    asst_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=agent_response.final_output,
        agent_trace=trace_data,
        model_used=agent_response.model_used,
        provider_used=agent_response.provider_used,
        tokens_completion=agent_response.total_tokens,
        latency_ms=agent_response.total_latency_ms,
        is_fallback=agent_response.is_fallback
    )
    db.add(asst_msg)

    # 5. Record Telemetry
    cost_usd = round(agent_response.total_tokens * 0.0000007, 6)
    telemetry = TelemetryLog(
        endpoint="/api/agent/run",
        query=payload.task,
        provider=agent_response.provider_used,
        model=agent_response.model_used,
        total_tokens=agent_response.total_tokens,
        estimated_cost_usd=cost_usd,
        latency_ms=agent_response.total_latency_ms,
        fallback_triggered=agent_response.is_fallback,
        status_code=200
    )
    db.add(telemetry)
    await db.commit()

    return agent_response
