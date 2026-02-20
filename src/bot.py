"""Telegram bot handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
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
from src.sheets import get_medicines
from src.settings import settings

logger = logging.getLogger(__name__)

_ai: AIClient | None = None


def get_ai() -> AIClient:
    global _ai
    if _ai is None:
        _ai = create_ai_client()
    return _ai


# --------------- /start ---------------

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

ASK_WHO = "Кто болеет — взрослый или ребёнок?"

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


# --------------- Core processing ---------------

async def _process_query(query: ExtractedQuery, update: Update) -> None:
    """Process an extracted query and send the response."""
    msg = update.message
    assert msg is not None

    if query.intent == Intent.OTHER:
        await msg.reply_text(
            "Я помогаю только с подбором лекарств из аптечки. "
            "Опишите симптомы или спросите, что есть в аптечке."
        )
        return

    if query.person == PersonType.UNKNOWN and query.intent == Intent.WHAT_TO_TAKE:
        await msg.reply_text(ASK_WHO)
        return

    medicines = get_medicines()
    results = match_medicines(query, medicines)

    prefix = ""
    if has_red_flags(query):
        prefix = RED_FLAG_PREFIX

    if query.intent == Intent.INVENTORY_QUERY:
        text = format_inventory_query(query, results)
    else:
        text = format_what_to_take(query, results)

    await msg.reply_text(prefix + text)


# --------------- Text handler ---------------

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

        await _process_query(query, update)
    except Exception:
        logger.exception("Error in handle_text")
        await msg.reply_text("Произошла ошибка. Попробуйте ещё раз чуть позже.")


# --------------- Voice handler ---------------

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

        await _process_query(query, update)
    except Exception:
        logger.exception("Error in handle_voice")
        await msg.reply_text("Произошла ошибка. Попробуйте ещё раз чуть позже.")


# --------------- Build application ---------------

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
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app
