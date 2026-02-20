"""NLU orchestration: voice → text → structured extraction."""

from __future__ import annotations

import logging

from src.ai_client.base import AIClient
from src.models import ExtractedQuery

logger = logging.getLogger(__name__)


async def transcribe_voice(ai: AIClient, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str | None:
    """Attempt voice-to-text transcription. Returns None if provider doesn't support it."""
    try:
        text = await ai.transcribe_audio(audio_bytes, mime_type)
        return text.strip() if text else None
    except NotImplementedError:
        logger.info("AI provider does not support transcription")
        return None
    except Exception:
        logger.exception("Transcription failed")
        return None


async def extract_query(ai: AIClient, text: str) -> ExtractedQuery | None:
    """Run structured NLU extraction. Returns None on unrecoverable failure."""
    try:
        return await ai.extract_structured(text)
    except Exception:
        logger.exception("NLU extraction failed after retries")
        return None
