"""Text normalisation utilities for Russian medical text."""

from __future__ import annotations

import re
import unicodedata


def normalize_russian(text: str) -> str:
    """Lowercase, ё→е, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    return normalize_russian(text).split()
