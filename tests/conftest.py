"""Shared fixtures for tests."""

from __future__ import annotations

import datetime
import os

import pytest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test:token")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("PUBLIC_BASE_URL", "https://test.example.com")
os.environ.setdefault("AI_PROVIDER", "generic_http")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", "test.json")
os.environ.setdefault("GOOGLE_SHEET_ID", "test-sheet-id")

from src.models import Medicine


@pytest.fixture
def sample_medicines() -> list[Medicine]:
    return [
        Medicine(
            name="Нурофен",
            active_substance="ибупрофен",
            form="таблетки",
            target="взрослые",
            category="обезболивающее",
            symptoms="головная боль, температура, зубная боль",
            child_safe=False,
            expiration=datetime.date(2027, 12, 1),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Нурофен Детский",
            active_substance="ибупрофен",
            form="сироп",
            target="дети",
            category="обезболивающее",
            symptoms="температура, боль, головная боль",
            child_safe=True,
            expiration=datetime.date(2027, 6, 1),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Гексорал",
            active_substance="гексэтидин",
            form="спрей",
            target="все",
            category="горло",
            symptoms="боль в горле, ангина, фарингит",
            child_safe=True,
            expiration=datetime.date(2026, 10, 1),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Амоксиклав",
            active_substance="амоксициллин + клавулановая кислота",
            form="таблетки",
            target="взрослые",
            category="антибиотик",
            symptoms="бактериальная инфекция, отит, синусит",
            child_safe=False,
            expiration=datetime.date(2026, 8, 1),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Maxitrol",
            active_substance="дексаметазон + неомицин + полимиксин",
            form="глазные капли",
            target="взрослые",
            category="глазные капли",
            symptoms="конъюнктивит, воспаление глаз",
            child_safe=False,
            expiration=datetime.date(2027, 1, 1),
            comment="ВРАЧ",
            status="Активен",
        ),
        Medicine(
            name="Смекта",
            active_substance="диосмектит",
            form="порошок",
            target="все",
            category="ЖКТ",
            symptoms="диарея, понос, тошнота, рвота, желудок",
            child_safe=True,
            expiration=datetime.date(2027, 3, 1),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Coldrex",
            active_substance="парацетамол + фенилэфрин + витамин C",
            form="порошок",
            target="взрослые",
            category="простуда",
            symptoms="температура, насморк, головная боль, простуда",
            child_safe=False,
            expiration=datetime.date(2028, 5, 15),
            comment="",
            status="Активен",
        ),
        Medicine(
            name="Просроченный",
            active_substance="тест",
            form="тест",
            target="все",
            category="тест",
            symptoms="тест",
            child_safe=True,
            expiration=datetime.date(2020, 1, 1),
            comment="",
            status="Активен",
        ),
    ]
