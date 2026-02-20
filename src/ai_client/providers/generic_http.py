"""GenericHTTPProvider — works with any AI backend that exposes /transcribe and /extract."""

from __future__ import annotations

import json
import logging

import httpx

from src.ai_client.base import AIClient
from src.ai_client.schemas import NLU_EXTRACTION_SCHEMA, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.models import ExtractedQuery
from src.settings import settings

logger = logging.getLogger(__name__)


class GenericHTTPProvider(AIClient):
    """
    Expects two endpoints at AI_BASE_URL:

    POST /transcribe
      Body: multipart/form-data  file=<audio_bytes>
      Response: {"text": "transcribed text"}

    POST /extract
      Body: {"system": "...", "user": "...", "schema": {...}}
      Response: JSON matching NLU_EXTRACTION_SCHEMA
    """

    def __init__(self) -> None:
        self._base = settings.ai_base_url.rstrip("/")
        self._timeout = settings.ai_timeout_seconds
        self._retries = settings.ai_max_retries
        headers: dict[str, str] = {"Accept": "application/json"}
        if settings.ai_api_key:
            headers["Authorization"] = f"Bearer {settings.ai_api_key}"
        self._headers = headers

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers=self._headers,
        )

    # ---- transcribe ----

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        ext = mime_type.split("/")[-1]
        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(
                        f"{self._base}/transcribe",
                        files={"file": (f"voice.{ext}", audio_bytes, mime_type)},
                    )
                    resp.raise_for_status()
                    return resp.json().get("text", "")
                except Exception:
                    logger.warning("transcribe attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
        return ""

    # ---- extract ----

    async def extract_structured(self, text: str) -> ExtractedQuery:
        payload = {
            "system": SYSTEM_PROMPT,
            "user": USER_PROMPT_TEMPLATE.format(text=text),
            "schema": NLU_EXTRACTION_SCHEMA,
        }
        if settings.ai_model:
            payload["model"] = settings.ai_model

        async with self._client() as client:
            for attempt in range(1, self._retries + 2):
                try:
                    resp = await client.post(
                        f"{self._base}/extract",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return ExtractedQuery.model_validate(data)
                except Exception:
                    logger.warning("extract attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
        return ExtractedQuery()
