"""MiniMaxProvider — HTTP-based integration with MiniMax API."""

from __future__ import annotations

import json
import logging

import httpx

from src.ai_client.base import AIClient
from src.ai_client.schemas import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.models import ExtractedQuery
from src.settings import settings

logger = logging.getLogger(__name__)


class MiniMaxProvider(AIClient):
    def __init__(self) -> None:
        self._retries = settings.ai_max_retries
        self._model = settings.ai_model or "abab6.5s-chat"
        self._base = (settings.ai_base_url or "https://api.minimax.chat").rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(settings.ai_timeout_seconds),
            headers=self._headers,
        )

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        ext = mime_type.split("/")[-1]
        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(
                        f"{self._base}/v1/audio/transcriptions",
                        files={"file": (f"voice.{ext}", audio_bytes, mime_type)},
                        data={"model": "speech-to-text"},
                    )
                    resp.raise_for_status()
                    return resp.json().get("text", "")
                except Exception:
                    logger.warning("minimax transcribe attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
        return ""

    async def extract_structured(self, text: str) -> ExtractedQuery:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)},
            ],
            "response_format": {"type": "json_object"},
        }
        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(
                        f"{self._base}/v1/text/chatcompletion_v2",
                        json=payload,
                    )
                    resp.raise_for_status()
                    body = resp.json()
                    raw_text = body["choices"][0]["message"]["content"]
                    data = json.loads(raw_text)
                    return ExtractedQuery.model_validate(data)
                except Exception:
                    logger.warning("minimax extract attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
        return ExtractedQuery()
