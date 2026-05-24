"""Telegram bot handlers."""

from __future__ import annotations

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.ai_client import create_ai_client
from src.ai_client.base import AIClient
from src.matcher import (
    format_inventory_query,
    format_what_to_take,
    match_medicines,
)
from src.models import ExtractedQuery, Intent, PersonType
from src.nlu import extract_query, transcribe_voice
from src.safety import has_red_flags
from src.sheets import get_medicines, get_sheet_status
from src.settings import settings

logger = logging.getLogger(__name__)

_ai: AIClient | None = None

_ADULT_PATTERN = re.compile(
    r"^(взрослый|взрослая|взрослого|для\s+взрослого|я|себе|мне|для\s+меня|для\s+себя)$",
    re.IGNORECASE,
)
_CHILD_PATTERN = re.compile(
    r"^(ребёнок|ребенок|ребенку|ребёнку|дитя|для\s+ребёнка|для\s+ребенка|малыш|сын|дочь|дочка|дочке|сыну|малышу)$",
    re.IGNORECASE,
)


def get_ai() -> AIClient:
    global _ai
    if _ai is None:
        _ai = create_ai_client()
    return _ai


START_TEXT = (
    "Привет! Я помогу подобрать лекарство из домашней аптечки.\n\n"
    "Опишите симптомы текстом или голосовым сообщением, например:\n"
    "• «у ребёнка болит горло и температура»\n"
    "• «что выпить от головы»\n"
    "• «что есть от желудка»\n\n"
    "⚠️ Я НЕ ставлю диагнозы и НЕ назначаю лечение.\n"
    "Я только показываю, что есть в вашей аптечке."
)

HELP_TEXT = (
    "Как спрашивать:\n\n"
    "• Напишите или скажите симптомы: «болит голова», «у ребёнка кашель»\n"
    "• Спросите, что есть: «что есть от температуры»\n"
    "• Уточните, кто болеет: взрослый или ребёнок\n\n"
    "Команды:\n"
    "/start — о боте\n"
    "/help — как пользоваться\n"
    "/inventory — примеры запросов"
)

INVENTORY_TEXT = (
    "Примеры запросов к аптечке:\n\n"
    "• «что есть от температуры»\n"
    "• «что есть от горла»\n"
    "• «покажи лекарства от кашля»\n"
    "• «есть ли что-то от аллергии»"
)

ASK_WHO = "Кто болеет — взрослый или ребёнок (возраст)?"

RED_FLAG_PREFIX = "⚠️ Лучше обратиться к врачу или вызвать скорую помощь.\n\n"

TRANSCRIBE_FALLBACK = (
    "К сожалению, не удалось распознать голосовое сообщение. "
    "Пожалуйста, напишите симптомы текстом."
)

NLU_FALLBACK = (
    "Не удалось разобрать запрос. Попробуйте описать симптомы иначе, например:\n"
    "«болит голова» или «у ребёнка температура»."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT)  # type: ignore[union-attr]


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)  # type: ignore[union-attr]


async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(INVENTORY_TEXT)  # type: ignore[union-attr]


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show matching debug info for a symptom."""
    msg = update.message
    assert msg is not None
    parts = (msg.text or "").split(maxsplit=1)
    symptom = parts[1].strip() if len(parts) > 1 else "температура"

    medicines = get_medicines()
    child_safe_all = [m for m in medicines if m.child_safe]
    from src.matcher import _expand_symptoms, _score_medicine, _SCORE_THRESHOLD
    expanded = _expand_symptoms([symptom])
    matched_all = [(m, _score_medicine(m, expanded)) for m in medicines]
    matched_all = [(m, s) for m, s in matched_all if s >= _SCORE_THRESHOLD]
    matched_child = [(m, s) for m, s in matched_all if m.child_safe]

    lines = [
        f"🔍 Симптом: <b>{symptom}</b>",
        f"Всего лекарств: {len(medicines)}",
        f"Детских (child_safe=да): {len(child_safe_all)}",
        f"Матчей по симптому: {len(matched_all)}",
        f"Детских матчей: {len(matched_child)}",
        "",
    ]
    if matched_child:
        lines.append("Детские совпадения:")
        for m, s in matched_child[:5]:
            lines.append(f"• {m.name} ({m.form}) — score {s:.0f}")
    elif matched_all:
        lines.append("Взрослые совпадения (без детских):")
        for m, s in matched_all[:5]:
            lines.append(f"• {m.name} child_safe={m.child_safe} score={s:.0f}")
    else:
        lines.append("❌ Вообще нет совпадений")
        lines.append(f"Expanded: {expanded[:5]}")
        # show sample med texts
        for m in medicines[:3]:
            from src.utils import normalize_russian
            lines.append(f"  sample: '{normalize_russian(m.symptoms + ' ' + m.category)[:60]}'")

    await msg.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force-reload Google Sheets and report status."""
    msg = update.message
    assert msg is not None
    await msg.reply_text("🔄 Перезагружаю данные из Google Sheets…")
    get_medicines(force_refresh=True)
    count, error = get_sheet_status()
    if error:
        await msg.reply_text(
            f"❌ Ошибка загрузки таблицы:\n<code>{error[:400]}</code>",
            parse_mode="HTML",
        )
    else:
        await msg.reply_text(f"✅ Загружено {count} лекарств из таблицы.")


async def _process_query(query: ExtractedQuery, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process an extracted query and send the response."""
    msg = update.message
    assert msg is not None

    if query.intent == Intent.OTHER:
        await msg.reply_text(
            "Я помогаю только с подбором лекарств из аптечки. "
            "Опишите симптомы или спросите, что есть в аптечке."
        )
        return

    # Serverless-safe follow-up: encode query in callback_data, no memory needed.
    if query.person == PersonType.UNKNOWN and query.intent == Intent.WHAT_TO_TAKE:
        symptoms_str = ",".join(query.symptoms)[:50]  # keep under 64-byte limit
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👶 Ребёнок", callback_data=f"who:child:{symptoms_str}"),
                InlineKeyboardButton("🧑 Взрослый", callback_data=f"who:adult:{symptoms_str}"),
            ]
        ])
        await msg.reply_text("Кто болеет — ребёнок или взрослый?", reply_markup=keyboard)
        return

    medicines = get_medicines()

    # If sheet failed to load — tell the user explicitly instead of "not found"
    if not medicines:
        _, sheet_error = get_sheet_status()
        if sheet_error:
            await msg.reply_text(
                "⚠️ Не удалось загрузить аптечку из Google Sheets.\n"
                f"Ошибка: <code>{sheet_error[:200]}</code>",
                parse_mode="HTML",
            )
            return

    results = match_medicines(query, medicines)

    prefix = ""
    if has_red_flags(query):
        prefix = RED_FLAG_PREFIX

    if query.intent == Intent.INVENTORY_QUERY:
        text = format_inventory_query(query, results)
    else:
        text = format_what_to_take(query, results)

    await msg.reply_text(prefix + text)


def _try_resolve_person(text: str) -> PersonType | None:
    """Check if text is a short answer to 'who is sick?' question."""
    cleaned = text.strip().rstrip(".!?,;")
    if _ADULT_PATTERN.match(cleaned):
        return PersonType.ADULT
    if _CHILD_PATTERN.match(cleaned):
        return PersonType.CHILD
    return None


async def _handle_person_answer(
    person: PersonType,
    pending: ExtractedQuery,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """User answered the 'who is sick?' follow-up."""
    context.user_data.pop("pending_query", None)  # type: ignore[union-attr]
    pending.person = person
    await _process_query(pending, update, context)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.text:
        return

    try:
        ai = get_ai()
        query = await extract_query(ai, msg.text)
        if query is None:
            await msg.reply_text(NLU_FALLBACK)
            return

        await _process_query(query, update, context)
    except Exception:
        logger.exception("Error in handle_text")
        await msg.reply_text("Произошла ошибка. Попробуйте ещё раз чуть позже.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.voice:
        return

    try:
        voice = msg.voice
        file = await context.bot.get_file(voice.file_id)
        audio_bytes = await file.download_as_bytearray()

        ai = get_ai()
        transcript = await transcribe_voice(ai, bytes(audio_bytes), mime_type="audio/ogg")

        if not transcript:
            await msg.reply_text(TRANSCRIBE_FALLBACK)
            return

        query = await extract_query(ai, transcript)
        if query is None:
            await msg.reply_text(NLU_FALLBACK)
            return

        await _process_query(query, update, context)
    except Exception:
        logger.exception("Error in handle_voice")
        await msg.reply_text("Произошла ошибка. Попробуйте ещё раз чуть позже.")


async def handle_who_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for child/adult selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    data = query.data or ""
    # format: "who:child:симптом1,симптом2" or "who:adult:симптом1,симптом2"
    parts = data.split(":", 2)
    if len(parts) != 3 or parts[0] != "who":
        await query.edit_message_text("Что-то пошло не так. Попробуйте написать заново.")
        return

    _, person_str, symptoms_str = parts
    person = PersonType.CHILD if person_str == "child" else PersonType.ADULT
    symptoms = [s.strip() for s in symptoms_str.split(",") if s.strip()]

    medicines = get_medicines()
    if not medicines:
        _, sheet_error = get_sheet_status()
        if sheet_error:
            await query.edit_message_text(f"⚠️ Ошибка загрузки таблицы: {sheet_error[:200]}")
            return

    extracted = ExtractedQuery(symptoms=symptoms, intent=Intent.WHAT_TO_TAKE, person=person)
    results = match_medicines(extracted, medicines)

    prefix = "👶 Для ребёнка:\n" if person == PersonType.CHILD else "🧑 Для взрослого:\n"
    text = prefix + format_what_to_take(extracted, results)

    # Edit original message — no duplicate (per CLAUDE.md inline button rule)
    await query.edit_message_text(text)


def build_app() -> Application:
    """Build the telegram Application (webhook mode)."""
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("inventory", cmd_inventory))
    app.add_handler(CommandHandler("reload", cmd_reload))
    app.add_handler(CommandHandler("debug", cmd_debug))
    app.add_handler(CallbackQueryHandler(handle_who_callback, pattern=r"^who:"))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app
