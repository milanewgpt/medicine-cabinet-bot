from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import ExtractedQuery


class AIClient(ABC):
    """Provider-agnostic AI interface."""

    @abstractmethod
    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """Convert speech to text. Return transcript string."""

    @abstractmethod
    async def extract_structured(self, text: str) -> ExtractedQuery:
        """Run NLU extraction and return a validated pydantic model."""
