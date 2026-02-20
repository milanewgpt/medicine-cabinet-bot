"""FastAPI webhook server for the Telegram medicine-cabinet bot."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update

from src.bot import build_app
from src.settings import settings

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

tg_app = build_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await tg_app.initialize()
    await tg_app.start()

    webhook_url = settings.webhook_url
    await tg_app.bot.set_webhook(
        url=webhook_url,
        secret_token=settings.telegram_webhook_secret or None,
    )
    logger.info("Webhook set: %s", webhook_url)

    yield

    await tg_app.stop()
    await tg_app.shutdown()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    if settings.telegram_webhook_secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != settings.telegram_webhook_secret:
            return Response(status_code=403)

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
