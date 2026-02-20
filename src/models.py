from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------- NLU models ---------------

class PersonType(str, Enum):
    CHILD = "child"
    ADULT = "adult"
    UNKNOWN = "unknown"


class Intent(str, Enum):
    WHAT_TO_TAKE = "what_to_take"
    INVENTORY_QUERY = "inventory_query"
    OTHER = "other"


class ExtractedQuery(BaseModel):
    """Structured output from NLU extraction."""
    person: PersonType = PersonType.UNKNOWN
    child_age: Optional[int] = None
    symptoms_raw: str = ""
    symptoms: list[str] = Field(default_factory=list)
    temperature_c: Optional[float] = None
    duration_days: Optional[int] = None
    red_flags: list[str] = Field(default_factory=list)
    intent: Intent = Intent.WHAT_TO_TAKE


# --------------- Medicine models ---------------

class Medicine(BaseModel):
    """One row from the Google Sheet inventory."""
    name: str = ""                          # Название
    active_substance: str = ""              # Активное вещество
    form: str = ""                          # Форма
    target: str = ""                        # Для кого
    category: str = ""                      # Категория
    symptoms: str = ""                      # Симптомы
    child_safe: bool = False                # Детям можно  ("Да" → True)
    expiration: Optional[datetime.date] = None  # Срок годности
    comment: str = ""                       # Комментарий
    status: str = ""                        # Статус

    @property
    def is_active(self) -> bool:
        return self.status.strip().lower() == "активен"

    @property
    def is_expired(self) -> bool:
        if self.expiration is None:
            return False
        return self.expiration < datetime.date.today()

    @property
    def is_available(self) -> bool:
        return self.is_active and not self.is_expired


# --------------- Match result ---------------

class MatchResult(BaseModel):
    medicine: Medicine
    score: float = 0.0
    doctor_only: bool = False
    doctor_reason: str = ""
