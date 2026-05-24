"""Google Sheets reader with in-memory caching."""

from __future__ import annotations

import datetime
import logging
import time
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from src.models import Medicine
from src.settings import settings

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_cache: list[Medicine] = []
_cache_ts: float = 0.0
_CACHE_TTL = 300  # 5 minutes
_last_error: str = ""  # last fetch error message


def _parse_date(raw: str) -> Optional[datetime.date]:
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%Y"):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _row_to_medicine(row: dict[str, str]) -> Medicine:
    child_raw = row.get("Детям можно", "").strip().lower()
    return Medicine(
        name=row.get("Название", "").strip(),
        active_substance=row.get("Активное вещество", "").strip(),
        form=row.get("Форма", "").strip(),
        target=row.get("Для кого", "").strip(),
        category=row.get("Категория", "").strip(),
        symptoms=row.get("Симптомы", "").strip(),
        child_safe=(child_raw == "да"),
        expiration=_parse_date(row.get("Срок годности", "")),
        comment=row.get("Комментарий", "").strip(),
        status=row.get("Статус", "").strip(),
    )


def _fetch_all() -> list[Medicine]:
    if settings.google_service_account_json_content:
        import json
        info = json.loads(settings.google_service_account_json_content)
        creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            settings.google_service_account_json, scopes=_SCOPES,
        )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(settings.google_sheet_id)
    ws = sh.worksheet(settings.google_sheet_tab_name)
    rows = ws.get_all_records()
    medicines: list[Medicine] = []
    for row in rows:
        med = _row_to_medicine(row)
        if med.is_available:
            medicines.append(med)
    logger.info("Loaded %d active medicines from sheet", len(medicines))
    return medicines


def get_medicines(force_refresh: bool = False) -> list[Medicine]:
    global _cache, _cache_ts, _last_error
    now = time.time()
    if force_refresh or not _cache or (now - _cache_ts > _CACHE_TTL):
        try:
            _cache = _fetch_all()
            _cache_ts = now
            _last_error = ""
        except Exception as exc:
            _last_error = str(exc)
            logger.exception("Failed to refresh sheet data")
            if _cache:
                logger.warning("Using stale cache")
    return _cache


def get_sheet_status() -> tuple[int, str]:
    """Return (count_of_loaded_medicines, last_error_message).
    Empty error string means last load was successful.
    """
    return len(_cache), _last_error
