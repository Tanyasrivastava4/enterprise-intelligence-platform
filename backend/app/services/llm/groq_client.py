import time
from typing import Optional
from groq import AsyncGroq
from app.services.llm.base import BaseLLMClient, LLMResult
from app.core.config import settings

class GroqLLMClient(BaseLLMClient):

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        if not self.api_key:
            self.client = None
        else:
            self.client = AsyncGroq(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> LLMResult:
        if not self.client:
            raise ValueError("Groq API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        latency_ms = int((time.time() - start_time) * 1000)

        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        comp_tokens = usage.completion_tokens if usage else 0

        content = response.choices[0].message.content or ""

        return LLMResult(
            content=content,
            tokens_prompt=prompt_tokens,
            tokens_completion=comp_tokens,
            total_tokens=prompt_tokens + comp_tokens,
            model=self.model,
            provider="groq",
            latency_ms=latency_ms
        )
