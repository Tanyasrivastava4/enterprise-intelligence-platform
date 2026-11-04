import logging
from typing import Optional, Dict
from app.services.llm.base import BaseLLMClient, LLMResult
from app.services.llm.groq_client import GroqLLMClient
from app.services.llm.gemini_client import GeminiLLMClient
from app.services.llm.openai_client import OpenAILLMClient
from app.core.config import settings

logger = logging.getLogger("llm_router")

class ResilientLLMRouter:
    """Manages primary and secondary LLM providers with automatic fallback

    upon rate limits (429), timeouts, or API outages.
    """

    def __init__(self):
        self.providers: Dict[str, BaseLLMClient] = {}
        self._init_providers()

    def _init_providers(self):
        # Register available providers
        if settings.GROQ_API_KEY:
            self.providers["groq"] = GroqLLMClient(model=settings.GROQ_MODEL)
            self.providers["groq_fallback"] = GroqLLMClient(model=settings.GROQ_FALLBACK_MODEL)
        if settings.GEMINI_API_KEY:
            self.providers["gemini"] = GeminiLLMClient()
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAILLMClient()

    def get_provider_client(self, provider_name: str) -> Optional[BaseLLMClient]:
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        # Lazy initialization
        if provider_name == "groq" and settings.GROQ_API_KEY:
            self.providers["groq"] = GroqLLMClient()
            return self.providers["groq"]
        elif provider_name == "gemini" and settings.GEMINI_API_KEY:
            self.providers["gemini"] = GeminiLLMClient()
            return self.providers["gemini"]
        elif provider_name == "openai" and settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAILLMClient()
            return self.providers["openai"]
        return None

    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        preferred_provider: Optional[str] = None
    ) -> LLMResult:
        """Attempts primary provider, and upon error automatically switches to fallback provider."""
        primary_name = preferred_provider or settings.PRIMARY_LLM_PROVIDER
        fallback_name = settings.FALLBACK_LLM_PROVIDER if primary_name != settings.FALLBACK_LLM_PROVIDER else "openai"

        primary_client = self.get_provider_client(primary_name)
        fallback_client = self.get_provider_client(fallback_name)

        # Fallback to whatever provider is configured if preferred isn't available
        if not primary_client:
            for name, client in self.providers.items():
                if client:
                    primary_client = client
                    primary_name = name
                    break

        if not primary_client:
            raise RuntimeError("No LLM provider is configured with valid API keys. Please check your .env file.")

        try:
            # 1. Attempt Primary Provider
            result = await primary_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            result.is_fallback = False
            return result

        except Exception as primary_error:
            logger.warning(
                f"Primary LLM provider '{primary_name}' failed with error: {primary_error}. "
                f"Attempting fallback to '{fallback_name}'..."
            )

            # 2. Attempt Fallback Provider if available
            if fallback_client and fallback_name != primary_name:
                try:
                    result = await fallback_client.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    result.is_fallback = True
                    logger.info(f"Fallback to provider '{fallback_name}' was successful.")
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback provider '{fallback_name}' also failed: {fallback_error}")
                    raise RuntimeError(
                        f"Both primary provider '{primary_name}' ({primary_error}) and fallback provider '{fallback_name}' ({fallback_error}) failed."
                    )
            else:
                # No fallback configured or same as primary
                raise primary_error

llm_router = ResilientLLMRouter()
