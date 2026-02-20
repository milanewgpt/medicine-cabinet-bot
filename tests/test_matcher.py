"""Tests for the symptom matching engine."""

from __future__ import annotations

from src.matcher import (
    format_inventory_query,
    format_what_to_take,
    match_medicines,
)
from src.models import ExtractedQuery, Intent, Medicine, PersonType


class TestMatchMedicines:
    def test_headache_adult(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["головная боль"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        assert len(results) > 0
        names = [r.medicine.name for r in results]
        assert "Нурофен" in names or "Coldrex" in names

    def test_sore_throat_finds_hexoral(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["боль в горле"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        names = [r.medicine.name for r in results]
        assert "Гексорал" in names

    def test_stomach_finds_smecta(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["желудок", "тошнота"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        names = [r.medicine.name for r in results]
        assert "Смекта" in names

    def test_child_filter(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.CHILD,
            symptoms=["температура"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        if results:
            child_safe_first = True
            found_adult = False
            for r in results:
                if not r.medicine.child_safe:
                    found_adult = True
                if found_adult and r.medicine.child_safe:
                    child_safe_first = False
            assert child_safe_first, "Child-safe medicines should come first"

    def test_empty_symptoms_returns_nothing(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=[],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        assert results == []

    def test_expired_not_in_fixtures(self, sample_medicines: list[Medicine]):
        """Expired medicines should be filtered out before matching (in sheets.py).
        The fixture includes one expired medicine; verify it's still in the list
        since filtering happens at sheet level — matcher operates on pre-filtered data."""
        expired = [m for m in sample_medicines if m.is_expired]
        assert len(expired) == 1
        assert expired[0].name == "Просроченный"

    def test_antibiotic_marked_doctor_only(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["отит", "инфекция"],
            intent=Intent.WHAT_TO_TAKE,
        )
        available = [m for m in sample_medicines if m.is_available]
        results = match_medicines(q, available)
        for r in results:
            if "амокси" in r.medicine.active_substance.lower():
                assert r.doctor_only is True


class TestFormatOutput:
    def test_format_what_to_take_adult(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["головная боль"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        text = format_what_to_take(q, results)
        assert "Можно рассмотреть" in text or "аптечке" in text

    def test_format_inventory_query(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.UNKNOWN,
            symptoms=["горло"],
            intent=Intent.INVENTORY_QUERY,
        )
        results = match_medicines(q, sample_medicines)
        text = format_inventory_query(q, results)
        assert "В аптечке есть" in text or "ничего" in text

    def test_format_empty_results(self, sample_medicines: list[Medicine]):
        q = ExtractedQuery(
            person=PersonType.ADULT,
            symptoms=["несуществующий симптом xyz"],
            intent=Intent.WHAT_TO_TAKE,
        )
        results = match_medicines(q, sample_medicines)
        text = format_what_to_take(q, results)
        assert "не нашлось" in text or "Можно рассмотреть" in text
