"""Tests for text normalisation utilities."""

from src.utils import normalize_russian, tokenize


class TestNormalize:
    def test_lowercase(self):
        assert normalize_russian("ТЕСТ") == "тест"

    def test_yo_to_ye(self):
        assert normalize_russian("ребёнок") == "ребенок"

    def test_strip_punctuation(self):
        assert normalize_russian("горло, нос!") == "горло нос"

    def test_collapse_whitespace(self):
        assert normalize_russian("  болит   голова  ") == "болит голова"

    def test_combined(self):
        assert normalize_russian("Ребёнок — КАШЕЛЬ!") == "ребенок кашель"


class TestTokenize:
    def test_simple(self):
        assert tokenize("болит голова") == ["болит", "голова"]

    def test_with_punctuation(self):
        assert tokenize("горло, температура!") == ["горло", "температура"]
