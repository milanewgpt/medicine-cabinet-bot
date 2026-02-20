from __future__ import annotations

from src.ai_client.base import AIClient
from src.settings import settings


def create_ai_client() -> AIClient:
    provider = settings.ai_provider.lower().strip()

    if provider == "gemini":
        from src.ai_client.providers.gemini import GeminiProvider
        return GeminiProvider()

    if provider == "minimax":
        from src.ai_client.providers.minimax import MiniMaxProvider
        return MiniMaxProvider()

    from src.ai_client.providers.generic_http import GenericHTTPProvider
    return GenericHTTPProvider()
