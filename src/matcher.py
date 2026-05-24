"""Symptom matching engine using RapidFuzz scoring."""

from __future__ import annotations

from rapidfuzz import fuzz

from src.models import (
    ExtractedQuery,
    Intent,
    MatchResult,
    Medicine,
    PersonType,
)
from src.safety import enrich_match_results
from src.utils import normalize_russian

# --------------- Synonym map ---------------

SYNONYMS: dict[str, list[str]] = {
    "температура": ["жар", "лихорадка", "высокая температура"],
    "простуда": ["орви", "орз", "грипп"],
    "боль в горле": ["горло", "горло болит", "ангина", "фарингит"],
    "насморк": ["заложенность", "заложенность носа", "сопли", "ринит"],
    "головная боль": ["голова", "болит голова", "мигрень"],
    "диарея": ["понос", "жидкий стул"],
    "тошнота": ["рвота", "тошнит", "мутит"],
    "жкт": ["желудок", "живот", "боль в животе", "кишечник", "гастрит"],
    "кашель": ["сухой кашель", "мокрый кашель", "покашливание"],
    "аллергия": ["аллергическая реакция", "крапивница", "зуд", "чешется"],
    "боль": ["болит", "ноет", "ломит"],
    "ожог": ["обжег", "обожгла", "ожёг"],
    "порез": ["рана", "царапина", "порезался"],
    "ушиб": ["синяк", "ударился", "удар"],
    "конъюнктивит": ["глаза красные", "глаз воспалился", "глаза гноятся"],
    "отит": ["ухо болит", "ушная боль", "боль в ухе", "уши", "ухо", "ушки"],
    "изжога": ["жжение в груди", "кислота"],
    "запор": ["не ходит в туалет"],
}

_SCORE_THRESHOLD = 55.0
_TOP_N = 5


def _expand_symptoms(symptoms: list[str]) -> list[str]:
    """Expand user symptoms through synonym mapping."""
    expanded: set[str] = set()
    for s in symptoms:
        norm = normalize_russian(s)
        expanded.add(norm)
        for canonical, aliases in SYNONYMS.items():
            all_forms = [normalize_russian(canonical)] + [normalize_russian(a) for a in aliases]
            if norm in all_forms or any(norm in f or f in norm for f in all_forms):
                expanded.add(normalize_russian(canonical))
                for a in aliases:
                    expanded.add(normalize_russian(a))
    return list(expanded)


def _score_medicine(med: Medicine, expanded_symptoms: list[str]) -> float:
    """Score a medicine against expanded symptoms using fuzzy matching."""
    med_text = normalize_russian(f"{med.symptoms} {med.category}")
    if not med_text.strip():
        return 0.0

    best_score = 0.0
    for sym in expanded_symptoms:
        # Skip very short terms — fuzz gives false positives on 2-3 char Cyrillic words
        if len(sym) < 4:
            continue
        score = fuzz.partial_ratio(sym, med_text)
        if score > best_score:
            best_score = score

    return best_score


def match_medicines(
    query: ExtractedQuery,
    medicines: list[Medicine],
) -> list[MatchResult]:
    """
    Match user query to medicines.
    Returns top candidates sorted by score, with doctor-only flags.
    """
    if not query.symptoms:
        return []

    expanded = _expand_symptoms(query.symptoms)
    if not expanded:
        return []

    is_child = query.person == PersonType.CHILD

    scored: list[MatchResult] = []
    for med in medicines:
        score = _score_medicine(med, expanded)
        if score >= _SCORE_THRESHOLD:
            scored.append(MatchResult(medicine=med, score=score))

    scored.sort(key=lambda r: r.score, reverse=True)
    scored = scored[:_TOP_N]
    scored = enrich_match_results(scored)

    if is_child:
        child_safe = [r for r in scored if r.medicine.child_safe]
        adult_only = [r for r in scored if not r.medicine.child_safe]
        return child_safe + adult_only

    return scored


# --------------- Format output ---------------

def _med_label(r: MatchResult) -> str:
    """Name + form (if set) + symptoms/category hint."""
    name = r.medicine.name
    form = f" ({r.medicine.form})" if r.medicine.form else ""
    hint = r.medicine.symptoms or r.medicine.category
    return f"• {name}{form} — {hint}"

def format_what_to_take(
    query: ExtractedQuery,
    results: list[MatchResult],
) -> str:
    """Format the response for a 'what_to_take' intent."""
    is_child = query.person == PersonType.CHILD

    if not results:
        return "К сожалению, подходящих лекарств в аптечке не нашлось."

    lines: list[str] = []

    if is_child:
        child_safe = [r for r in results if r.medicine.child_safe and not r.doctor_only]
        child_doc = [r for r in results if r.medicine.child_safe and r.doctor_only]
        adult_only = [r for r in results if not r.medicine.child_safe and not r.doctor_only]
        adult_doc = [r for r in results if not r.medicine.child_safe and r.doctor_only]

        if child_safe:
            lines.append("Можно рассмотреть (детям):")
            for r in child_safe:
                lines.append(_med_label(r))

        if child_doc:
            lines.append("\nТолько по назначению врача (детям):")
            for r in child_doc:
                lines.append(f"• {r.medicine.name}")

        if not child_safe and not child_doc:
            lines.append("Детских лекарств в аптечке не нашлось.")
            if adult_only or adult_doc:
                lines.append("\nВ аптечке есть только взрослое средство:")
                for r in adult_only:
                    lines.append(_med_label(r))
                for r in adult_doc:
                    lines.append(f"• {r.medicine.name} (только по назначению врача)")
    else:
        # PersonType.ADULT
        regular = [r for r in results if not r.doctor_only]
        doc_only = [r for r in results if r.doctor_only]

        if regular:
            lines.append("Можно рассмотреть:")
            for r in regular:
                lines.append(_med_label(r))

        if doc_only:
            lines.append("\nТолько по назначению врача:")
            for r in doc_only:
                lines.append(f"• {r.medicine.name}")

    return "\n".join(lines)


def format_inventory_query(
    query: ExtractedQuery,
    results: list[MatchResult],
) -> str:
    """Format the response for an 'inventory_query' intent."""
    if not results:
        return "По этим симптомам в аптечке ничего не нашлось."

    child_safe = [r for r in results if r.medicine.child_safe and not r.doctor_only]
    adult_only = [r for r in results if not r.medicine.child_safe and not r.doctor_only]
    doc_only = [r for r in results if r.doctor_only]

    lines: list[str] = ["В аптечке есть:"]

    if child_safe:
        lines.append("\nМожно детям:")
        for r in child_safe:
            lines.append(f"• {r.medicine.name} — {r.medicine.symptoms or r.medicine.category}")

    if adult_only:
        lines.append("\nТолько взрослым:")
        for r in adult_only:
            lines.append(f"• {r.medicine.name} — {r.medicine.symptoms or r.medicine.category}")

    if doc_only:
        lines.append("\nТолько по назначению врача:")
        for r in doc_only:
            lines.append(f"• {r.medicine.name}")

    return "\n".join(lines)
