"""Tests for pydantic models."""

from __future__ import annotations

import datetime

from src.models import ExtractedQuery, Intent, Medicine, PersonType


class TestMedicine:
    def test_is_active(self):
        m = Medicine(status="Активен")
        assert m.is_active is True

    def test_is_not_active(self):
        m = Medicine(status="Неактивен")
        assert m.is_active is False

    def test_is_expired(self):
        m = Medicine(expiration=datetime.date(2020, 1, 1), status="Активен")
        assert m.is_expired is True

    def test_is_not_expired(self):
        m = Medicine(expiration=datetime.date(2030, 1, 1), status="Активен")
        assert m.is_expired is False

    def test_no_expiration_not_expired(self):
        m = Medicine(status="Активен")
        assert m.is_expired is False

    def test_is_available(self):
        m = Medicine(status="Активен", expiration=datetime.date(2030, 1, 1))
        assert m.is_available is True

    def test_not_available_expired(self):
        m = Medicine(status="Активен", expiration=datetime.date(2020, 1, 1))
        assert m.is_available is False

    def test_not_available_inactive(self):
        m = Medicine(status="Неактивен")
        assert m.is_available is False

    def test_child_safe_flag(self):
        m = Medicine(child_safe=True, status="Активен")
        assert m.child_safe is True


class TestExtractedQuery:
    def test_defaults(self):
        q = ExtractedQuery()
        assert q.person == PersonType.UNKNOWN
        assert q.intent == Intent.WHAT_TO_TAKE
        assert q.symptoms == []
        assert q.red_flags == []

    def test_from_dict(self):
        data = {
            "person": "child",
            "child_age": 5,
            "symptoms_raw": "болит горло",
            "symptoms": ["боль в горле"],
            "temperature_c": 38.5,
            "duration_days": 2,
            "red_flags": [],
            "intent": "what_to_take",
        }
        q = ExtractedQuery.model_validate(data)
        assert q.person == PersonType.CHILD
        assert q.child_age == 5
        assert q.temperature_c == 38.5
