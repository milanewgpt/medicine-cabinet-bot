"""Tests for safety module: red-flag detection and doctor-only classification."""

from __future__ import annotations

from src.models import ExtractedQuery, Medicine, MatchResult
from src.safety import (
    classify_doctor_only,
    detect_red_flags_from_text,
    enrich_match_results,
    has_red_flags,
)


class TestRedFlags:
    def test_no_flags_in_normal_text(self):
        flags = detect_red_flags_from_text("болит голова")
        assert flags == []

    def test_breathing_difficulty(self):
        flags = detect_red_flags_from_text("ребёнок задыхается")
        assert len(flags) >= 1
        assert "задыхается" in flags

    def test_convulsions(self):
        flags = detect_red_flags_from_text("у ребенка судороги и температура")
        assert "судороги" in flags

    def test_blood_vomit(self):
        flags = detect_red_flags_from_text("рвота с кровью уже второй раз")
        assert "рвота с кровью" in flags

    def test_loss_of_consciousness(self):
        flags = detect_red_flags_from_text("человек потерял сознание")
        assert any("сознан" in f for f in flags)

    def test_has_red_flags_true(self):
        q = ExtractedQuery(red_flags=["судороги"])
        assert has_red_flags(q) is True

    def test_has_red_flags_false(self):
        q = ExtractedQuery(red_flags=[])
        assert has_red_flags(q) is False


class TestDoctorOnly:
    def test_comment_contains_doctor(self):
        med = Medicine(name="Test", comment="Только ВРАЧ", status="Активен")
        is_doc, reason = classify_doctor_only(med)
        assert is_doc is True
        assert "комментарий" in reason.lower() or "ВРАЧ" in reason

    def test_antibiotic_amoxicillin(self):
        med = Medicine(
            name="Амоксиклав",
            active_substance="амоксициллин",
            status="Активен",
        )
        is_doc, reason = classify_doctor_only(med)
        assert is_doc is True
        assert "антибиотик" in reason

    def test_antibiotic_azithromycin(self):
        med = Medicine(
            name="Азитромицин",
            active_substance="азитромицин",
            status="Активен",
        )
        is_doc, reason = classify_doctor_only(med)
        assert is_doc is True

    def test_antibiotic_ciprofloxacin(self):
        med = Medicine(
            name="Ципрофлоксацин",
            active_substance="ципрофлоксацин",
            status="Активен",
        )
        is_doc, reason = classify_doctor_only(med)
        assert is_doc is True

    def test_antibiotic_cephalosporin(self):
        med = Medicine(
            name="Цефтриаксон",
            active_substance="цефтриаксон",
            status="Активен",
        )
        is_doc, reason = classify_doctor_only(med)
        assert is_doc is True

    def test_maxitrol_doctor_by_comment(self):
        med = Medicine(
            name="Maxitrol",
            active_substance="дексаметазон + неомицин + полимиксин",
            comment="ВРАЧ",
            status="Активен",
        )
        is_doc, _ = classify_doctor_only(med)
        assert is_doc is True

    def test_regular_medicine_not_doctor_only(self):
        med = Medicine(
            name="Нурофен",
            active_substance="ибупрофен",
            comment="",
            status="Активен",
        )
        is_doc, _ = classify_doctor_only(med)
        assert is_doc is False

    def test_enrich_results(self):
        results = [
            MatchResult(
                medicine=Medicine(
                    name="Амоксиклав",
                    active_substance="амоксициллин",
                    status="Активен",
                ),
                score=80.0,
            ),
            MatchResult(
                medicine=Medicine(
                    name="Нурофен",
                    active_substance="ибупрофен",
                    status="Активен",
                ),
                score=75.0,
            ),
        ]
        enriched = enrich_match_results(results)
        assert enriched[0].doctor_only is True
        assert enriched[1].doctor_only is False
