"""JSON schema definitions used in NLU extraction prompts."""

from __future__ import annotations

NLU_EXTRACTION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "person": {
            "type": "string",
            "enum": ["child", "adult", "unknown"],
            "description": "Who is sick: child, adult, or unknown.",
        },
        "child_age": {
            "type": ["integer", "null"],
            "description": "Child age in years if mentioned, else null.",
        },
        "symptoms_raw": {
            "type": "string",
            "description": "Original symptom text as user said it.",
        },
        "symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Normalised symptom keywords in Russian.",
        },
        "temperature_c": {
            "type": ["number", "null"],
            "description": "Body temperature in Celsius if mentioned, else null.",
        },
        "duration_days": {
            "type": ["integer", "null"],
            "description": "How many days the symptoms last, else null.",
        },
        "red_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Life-threatening symptoms detected (breathing difficulty, convulsions, etc.).",
        },
        "intent": {
            "type": "string",
            "enum": ["what_to_take", "inventory_query", "other"],
            "description": "User intent.",
        },
    },
    "required": [
        "person", "child_age", "symptoms_raw", "symptoms",
        "temperature_c", "duration_days", "red_flags", "intent",
    ],
}

SYSTEM_PROMPT = """Ты — медицинский NLU-парсер для домашней аптечки.
Твоя задача — извлечь структурированные данные из фразы пользователя.

НЕ назначай лекарства. НЕ давай медицинских советов.
Только преобразуй текст в JSON по схеме.

Правила определения intent:
- "what_to_take" — пользователь спрашивает, что принять/выпить от симптома.
- "inventory_query" — пользователь хочет узнать, что есть в аптечке (фразы: «что есть», «покажи», «есть ли», «в аптечке», «список»).
- "other" — не связано с лекарствами.

Правила person:
- Если упоминается ребёнок, малыш, дочь, сын, дети — "child".
- Если контекст взрослого — "adult".
- Если не ясно — "unknown".

Red flags (запиши в red_flags если обнаружишь):
- затруднённое дыхание
- судороги
- сильное обезвоживание
- рвота с кровью
- сильная аллергическая реакция / отёк
- потеря сознания
- потеря зрения
- сильная головная боль с высокой температурой

Верни ТОЛЬКО валидный JSON. Никакого текста вне JSON."""

USER_PROMPT_TEMPLATE = "Фраза пользователя: {text}"
