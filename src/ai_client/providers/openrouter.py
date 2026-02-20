"""OpenRouterProvider — OpenAI-compatible API via openrouter.ai."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from src.ai_client.base import AIClient
from src.ai_client.schemas import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.models import ExtractedQuery
from src.settings import settings

logger = logging.getLogger(__name__)

_DEFAULT_BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider(AIClient):
    def __init__(self) -> None:
        self._retries = settings.ai_max_retries
        self._model = settings.ai_model or "google/gemini-2.5-flash"
        self._api_key = settings.ai_api_key
        self._base_url = (settings.ai_base_url or _DEFAULT_BASE).rstrip("/")
        self._timeout = settings.ai_timeout_seconds

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        raise NotImplementedError(
            "OpenRouter does not support standalone audio transcription. "
            "Use text input instead."
        )

    async def extract_structured(self, text: str) -> ExtractedQuery:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    body = resp.json()
                    raw = body["choices"][0]["message"]["content"]
                    data = json.loads(raw)
                    return ExtractedQuery.model_validate(data)
                except Exception:
                    logger.warning("openrouter attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return ExtractedQuery()
