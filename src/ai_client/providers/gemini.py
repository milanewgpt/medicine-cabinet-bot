"""GeminiProvider — pure HTTP integration with Google Gemini API."""

from __future__ import annotations

import asyncio
import base64
import json
import logging

import httpx

from src.ai_client.base import AIClient
from src.ai_client.schemas import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.models import ExtractedQuery
from src.settings import settings

logger = logging.getLogger(__name__)

_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIClient):
    def __init__(self) -> None:
        self._retries = settings.ai_max_retries
        self._model_name = settings.ai_model or "gemini-2.5-flash"
        self._api_key = settings.ai_api_key
        self._timeout = settings.ai_timeout_seconds

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        url = f"{_API_BASE}/{self._model_name}:generateContent?key={self._api_key}"
        audio_b64 = base64.standard_b64encode(audio_bytes).decode()
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Транскрибируй аудио на русском языке. Верни ТОЛЬКО текст, ничего больше."},
                    {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
                ],
            }],
        }
        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    body = resp.json()
                    return body["candidates"][0]["content"]["parts"][0]["text"].strip()
                except Exception:
                    logger.warning("gemini transcribe attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return ""

    async def extract_structured(self, text: str) -> ExtractedQuery:
        url = f"{_API_BASE}/{self._model_name}:generateContent?key={self._api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": USER_PROMPT_TEMPLATE.format(text=text)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }
        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    body = resp.json()
                    raw = body["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw)
                    return ExtractedQuery.model_validate(data)
                except Exception:
                    logger.warning("gemini http attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return ExtractedQuery()
