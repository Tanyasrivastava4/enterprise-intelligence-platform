from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LLMResult(BaseModel):
    content: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    model: str
    provider: str
    latency_ms: int = 0
    is_fallback: bool = False
    raw_response: Optional[Dict[str, Any]] = None

class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> LLMResult:
        pass
