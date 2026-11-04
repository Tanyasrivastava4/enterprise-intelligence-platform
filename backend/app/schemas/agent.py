from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AgentExecutionStep(BaseModel):
    step_number: int
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    latency_ms: int
    status: str = "success"  # success, error

class AgentTaskRequest(BaseModel):
    task: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    max_steps: int = 6

class AgentTaskResponse(BaseModel):
    conversation_id: str
    task: str
    final_output: str
    structured_report: Optional[Dict[str, Any]] = None
    steps: List[AgentExecutionStep]
    tools_used: List[str]
    total_steps: int
    total_latency_ms: int
    total_tokens: int
    model_used: str
    provider_used: str
    is_fallback: bool
    created_at: datetime
