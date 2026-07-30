# Open Family Medicine Cabinet

Open Family Medicine Cabinet is an open-source, privacy-first household medicine safety assistant.

It helps families understand what they already have at home, filter expired medicines, separate adult/child-safe items, and recognize red flags where self-care is unsafe.

It is **not** an AI doctor. It does **not** diagnose, prescribe treatment, or replace medical care.

Current implementation: a Telegram bot connected to a user-owned Google Sheets medicine inventory, with text/voice input, deterministic matching, expiry filtering, and safety rules.

## Why this exists

Most families have medicines at home, but the information is usually scattered across boxes, drawers, photos, chats, and memory.

Under stress, a parent or caregiver may need to know:

- What do we already have for fever, stomach pain, allergy, or a sore throat?
- Is this medicine expired?
- Is this marked as child-safe or adult-only?
- Is this a red-flag situation where we should seek medical care instead of self-treating?

This project makes household medicine information usable while keeping the source of truth under the user's control.

## What it does

- Stores the medicine cabinet inventory in a user-owned Google Sheet.
- Accepts text and voice requests in Telegram.
- Extracts the user's intent and symptoms with an AI provider, then keeps medicine selection deterministic.
- Matches symptoms to the household inventory with RapidFuzz and synonym expansion.
- Filters expired or inactive medicines before showing results.
- Separates adult/child suitability.
- Marks doctor-only items when configured in the inventory.
- Detects red flags and escalates to medical care instead of suggesting self-care.
- Uses webhook validation for Telegram requests.

## What it does not do

- It does not diagnose diseases.
- It does not prescribe medicines or dosages.
- It does not decide that self-care is safe.
- It does not replace a doctor, pharmacist, emergency service, or official medicine instructions.
- It does not require storing the family's medicine inventory in a proprietary health app.

## Architecture

```text
User (Telegram)
  -> FastAPI webhook
  -> Telegram handler
  -> text/voice understanding
  -> safety red-flag rules
  -> Google Sheets inventory reader
  -> deterministic matcher
  -> Telegram response
```

Key files:

- `src/main.py` — FastAPI app and Telegram webhook endpoint.
- `src/bot.py` — Telegram command and message handlers.
- `src/sheets.py` — Google Sheets inventory loader with caching.
- `src/nlu.py` — text/voice to structured query orchestration.
- `src/matcher.py` — deterministic medicine matching and response formatting.
- `src/safety.py` — red-flag and doctor-only safety logic.
- `src/models.py` — Pydantic models.
- `src/settings.py` — environment-based configuration.
- `api/index.py` — Vercel Python entrypoint.

## Current status

Working MVP / private household testing.

The production health endpoint is live:

```text
https://medicine-cabinet-bot-milanewgpts-projects.vercel.app/health
```

Public demo bot:

```text
https://t.me/medicine_home_bot
```

The MVP is currently Russian-first because it was built for a real family workflow. The project is designed to be translated and adapted for other households and communities.

## Inventory model

The current inventory backend is Google Sheets. Expected columns:

```text
Название
Активное вещество
Форма
Для кого
Категория
Симптомы
Детям можно
Срок годности
Комментарий
Статус
```

Safety-relevant fields:

- `Статус = Активен` — included in search.
- `Срок годности` — expired items are filtered out.
- `Детям можно = Да` — marked as child-safe.
- `Комментарий` containing `ВРАЧ` — marked as doctor-only.

## Safety model

The assistant is intentionally narrow. Its role is to organize household information and surface safety warnings, not to make medical decisions.

See:

- [`docs/safety-model.md`](docs/safety-model.md)
- [`docs/demo-flows.md`](docs/demo-flows.md)

Core safety rules:

- Always show that suggestions come from the user's own inventory.
- Filter expired medicines before matching.
- Separate adult/child-safe items.
- Highlight doctor-only items.
- Escalate red flags to medical care.
- Avoid diagnosis, prescriptions, dosage instructions, or certainty language.

## Bot commands

- `/start` — show the welcome message and usage guidance.
- `/help` — show available commands and safety notes.
- `/inventory` — show inventory examples / available categories.
- `/reload` — force reload of the Google Sheets inventory.
- `/debug <symptom>` — debug matching for a symptom query.

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Required production variables:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `PUBLIC_BASE_URL`
- `AI_PROVIDER`
- `AI_API_KEY` or provider-specific equivalent
- `GOOGLE_SHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` or `GOOGLE_SERVICE_ACCOUNT_JSON`

Do not commit real secrets.

## Local setup

```bash
git clone https://github.com/MilaArtyNew/medicine-cabinet-bot.git
cd medicine-cabinet-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Deployment

The current MVP is deployed as a Vercel Python serverless app.

- `vercel.json` routes requests to `api/index.py`.
- `api/index.py` imports the FastAPI app from `src.main`.
- Telegram sends updates to `/webhook`.
- `/health` returns a basic health check.

Production deployment requires environment variables to be configured in the hosting platform, not in Git.

## Roadmap

Grant/MVP v2 priorities:

- Make installation and first launch easier for non-technical users.
- Add a guided setup flow and clearer hosted/self-hosted options.
- Add an English sample inventory template.
- Add export/import flow for user-owned inventory files.
- Add language selection and multilingual interface support, starting with Russian and English; Hebrew later.
- Add a first-time medicine cabinet creation module: users send photos of medicine boxes/packages, the assistant extracts structured fields, asks follow-up questions when uncertain, and writes to the inventory only after user confirmation.
- Add more demo flows and safety test cases, including photo-based onboarding.
- Add optional local-first inventory backend for families that do not want Google Sheets.

See [`docs/roadmap.md`](docs/roadmap.md).

## Open-source scope

This repo contains the assistant logic, safety boundaries, integration code, and documentation. Families, caregivers, local communities, or developers can fork it, translate it, self-host it, or adapt it to a different inventory backend.

The open-source goal is not to build a centralized health platform. It is to make a small, auditable household safety tool that remains useful without depending on one vendor or one founder.

## Security and privacy

- Do not commit `.env` files, Telegram tokens, API keys, service account JSON files, or private sessions.
- User medicine inventory should remain under the user's control.
- The current implementation reads from a configured Google Sheet and does not require a project database.
- Telegram webhook requests are checked with `TELEGRAM_WEBHOOK_SECRET` when configured.

See [`SECURITY.md`](SECURITY.md).

## License

MIT License. See [`LICENSE`](LICENSE).
