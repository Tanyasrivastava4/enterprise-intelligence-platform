import time
from typing import Optional
import google.generativeai as genai
from app.services.llm.base import BaseLLMClient, LLMResult
from app.core.config import settings

class GeminiLLMClient(BaseLLMClient):

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        if self.api_key:
            genai.configure(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> LLMResult:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        start_time = time.time()
        
        # Configure model
        gemini_model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt if system_prompt else None
        )

        response = await gemini_model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        latency_ms = int((time.time() - start_time) * 1000)

        content = response.text if response and response.text else ""
        
        # Approximate tokens or extract usage metadata if available
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata:
            prompt_tokens = getattr(usage_metadata, "prompt_token_count", len(prompt.split()) * 2)
            comp_tokens = getattr(usage_metadata, "candidates_token_count", len(content.split()) * 2)
        else:
            prompt_tokens = len(prompt.split()) * 2
            comp_tokens = len(content.split()) * 2

        return LLMResult(
            content=content,
            tokens_prompt=prompt_tokens,
            tokens_completion=comp_tokens,
            total_tokens=prompt_tokens + comp_tokens,
            model=self.model,
            provider="gemini",
            latency_ms=latency_ms
        )
