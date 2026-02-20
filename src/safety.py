"""Safety module: red-flag detection and doctor-only classification."""

from __future__ import annotations

import re

from src.models import ExtractedQuery, Medicine, MatchResult
from src.utils import normalize_russian

# --------------- Red flags ---------------

RED_FLAGS_KEYWORDS: list[str] = [
    "затрудненное дыхание",
    "не может дышать",
    "задыхается",
    "судороги",
    "обезвоживание",
    "рвота с кровью",
    "кровавая рвота",
    "отек квинке",
    "анафилакс",
    "потеря сознания",
    "потерял сознание",
    "потеряла сознание",
    "потеря зрения",
    "потерял зрение",
    "потеряла зрение",
    "не видит",
    "сильная головная боль",
]


def detect_red_flags_from_text(text: str) -> list[str]:
    norm = normalize_russian(text)
    found: list[str] = []
    seen_canonical: set[str] = set()
    for kw in RED_FLAGS_KEYWORDS:
        if normalize_russian(kw) in norm:
            canonical = kw.split()[0]
            if canonical not in seen_canonical:
                found.append(kw)
                seen_canonical.add(canonical)
    return found


def has_red_flags(query: ExtractedQuery) -> bool:
    return bool(query.red_flags)


# --------------- Doctor-only ---------------

_ANTIBIOTIC_MARKERS = [
    "амокси", "азитро", "ципро", "цеф", "клавулан", "неомицин", "полимиксин",
]

_STEROID_EYE_PATTERNS = [
    re.compile(r"дексаметазон.*капл", re.IGNORECASE),
    re.compile(r"капл.*дексаметазон", re.IGNORECASE),
    re.compile(r"глаз.*стероид", re.IGNORECASE),
    re.compile(r"maxitrol", re.IGNORECASE),
]


def _is_antibiotic(med: Medicine) -> bool:
    combined = normalize_russian(f"{med.name} {med.active_substance}")
    return any(marker in combined for marker in _ANTIBIOTIC_MARKERS)


def _is_steroid_eye_drop(med: Medicine) -> bool:
    combined = f"{med.name} {med.active_substance} {med.form} {med.category}"
    return any(p.search(combined) for p in _STEROID_EYE_PATTERNS)


def _comment_says_doctor(med: Medicine) -> bool:
    return "врач" in med.comment.lower()


def classify_doctor_only(med: Medicine) -> tuple[bool, str]:
    """Returns (is_doctor_only, reason)."""
    if _comment_says_doctor(med):
        return True, "по комментарию: ВРАЧ"
    if _is_antibiotic(med):
        return True, "антибиотик"
    if _is_steroid_eye_drop(med):
        return True, "стероидные глазные капли"
    return False, ""


def enrich_match_results(results: list[MatchResult]) -> list[MatchResult]:
    """Add doctor_only flags to match results."""
    for r in results:
        is_doc, reason = classify_doctor_only(r.medicine)
        r.doctor_only = is_doc
        r.doctor_reason = reason
    return results
