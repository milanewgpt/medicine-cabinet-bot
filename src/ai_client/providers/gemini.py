"""GeminiProvider — uses Google Generative AI SDK or HTTP fallback."""

from __future__ import annotations

import json
import logging

import httpx

from src.ai_client.base import AIClient
from src.ai_client.schemas import NLU_EXTRACTION_SCHEMA, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.models import ExtractedQuery
from src.settings import settings

logger = logging.getLogger(__name__)

_SDK_AVAILABLE = False
try:
    import google.generativeai as genai  # type: ignore[import-untyped]
    _SDK_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]


class GeminiProvider(AIClient):
    def __init__(self) -> None:
        self._retries = settings.ai_max_retries
        self._model_name = settings.ai_model or "gemini-1.5-flash"
        if _SDK_AVAILABLE and settings.ai_api_key:
            genai.configure(api_key=settings.ai_api_key)  # type: ignore[union-attr]
            self._model = genai.GenerativeModel(  # type: ignore[union-attr]
                model_name=self._model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(  # type: ignore[union-attr]
                    response_mime_type="application/json",
                    response_schema=NLU_EXTRACTION_SCHEMA,
                ),
            )
        else:
            self._model = None

    # ---- transcribe (SDK does not support standalone STT; fallback) ----

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        if self._model is None:
            raise NotImplementedError("Gemini SDK not available for transcription")

        import asyncio

        def _sync_transcribe() -> str:
            response = self._model.generate_content([  # type: ignore[union-attr]
                "Transcribe the following audio to Russian text. Return ONLY the transcript, nothing else.",
                {"mime_type": mime_type, "data": audio_bytes},
            ])
            return response.text.strip()

        return await asyncio.get_event_loop().run_in_executor(None, _sync_transcribe)

    # ---- extract ----

    async def extract_structured(self, text: str) -> ExtractedQuery:
        if self._model is None:
            return await self._extract_via_http(text)
        return await self._extract_via_sdk(text)

    async def _extract_via_sdk(self, text: str) -> ExtractedQuery:
        import asyncio

        prompt = USER_PROMPT_TEMPLATE.format(text=text)

        def _sync_call() -> ExtractedQuery:
            for attempt in range(1, self._retries + 2):
                try:
                    response = self._model.generate_content(prompt)  # type: ignore[union-attr]
                    data = json.loads(response.text)
                    return ExtractedQuery.model_validate(data)
                except Exception:
                    logger.warning("gemini sdk attempt %d failed", attempt, exc_info=True)
                    if attempt > self._retries:
                        raise
            return ExtractedQuery()

        return await asyncio.get_event_loop().run_in_executor(None, _sync_call)

    async def _extract_via_http(self, text: str) -> ExtractedQuery:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={settings.ai_api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": USER_PROMPT_TEMPLATE.format(text=text)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": NLU_EXTRACTION_SCHEMA,
            },
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
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
        return ExtractedQuery()
