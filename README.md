# Medicine Cabinet Telegram Bot

Household medicine cabinet Telegram bot for tracking medicine inventory, expiry, reloads, and debug/status flows. It is allowed to include Russian user-facing examples because the family workflow is Russian-first.

## Features

- Tracks medicine cabinet inventory and related household items.
- Provides Telegram commands for inventory, reload, debug, help, and start.
- Supports Russian-first household usage while keeping setup/config documentation clear.

## Architecture

- **Repository:** `MilaArtyNew/medicine-cabinet-bot`
- **Primary stack:** Node.js / TypeScript / JavaScript, Python, systemd, Vercel
- **Entrypoints and scripts:**
  - `src/main.py`
  - `src/bot.py`
  - `npm script `rag`: `node rag.js``
- **Notable dependencies:** `fastapi`, `google-auth`, `google-generativeai`, `gspread`, `httpx`, `pydantic`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `python-dateutil`, `python-dotenv`, `python-telegram-bot[webhooks]`, `rapidfuzz`, `uvicorn[standard]`

## Configuration

Configure the service with environment variables. Do not commit real secrets to the repository.

- `AI_API_KEY` — required or optional runtime configuration. See deployment environment for the actual value.
- `AI_BASE_URL` — required or optional runtime configuration. See deployment environment for the actual value.
- `AI_PROVIDER` — required or optional runtime configuration. See deployment environment for the actual value.
- `GOOGLE_SHEET_ID` — required or optional runtime configuration. See deployment environment for the actual value.
- `MINIMAX_API_KEY` — required or optional runtime configuration. See deployment environment for the actual value.
- `PUBLIC_BASE_URL` — required or optional runtime configuration. See deployment environment for the actual value.
- `TELEGRAM_BOT_TOKEN` — required or optional runtime configuration. See deployment environment for the actual value.
- `TELEGRAM_WEBHOOK_SECRET` — required or optional runtime configuration. See deployment environment for the actual value.

## Setup

```bash
git clone https://github.com/MilaArtyNew/medicine-cabinet-bot
cd medicine-cabinet-bot
npm install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

Available npm scripts:
```bash
npm run rag
```

## Bot Commands

- `/debug` — Run debug output.
- `/help` — Show help and available commands.
- `/inventory` — Show inventory.
- `/reload` — Reload configuration or data.
- `/start` — Start the bot and show the main entry message.

If a command requires extra input and the argument is missing, the bot should ask a follow-up question instead of failing silently.

## Deployment Notes

- Keep secrets in the deployment platform environment variables, not in Git.
- Use the default branch as the source of truth for deployments.
- Check logs after every deployment and verify the `/status` or health endpoint when available.
- If the project uses a scheduler, verify timezone assumptions and idempotency before enabling it in production.

## Operational Notes

- Review logs after startup for missing environment variables or API authentication errors.
- Keep command names in English and document every user-facing command in this README.
- For Telegram bots, `/help` should list the same commands documented here.
- Inline buttons should edit the original message with the final status rather than sending duplicate messages.

## Troubleshooting

- **Bot does not respond:** verify the bot token, webhook/polling mode, and chat permissions.
- **Missing data:** check API keys, rate limits, and upstream service status.
- **Deployment starts but exits:** inspect platform logs for missing environment variables or import errors.
- **Commands differ from README:** update the command list here and in the bot command menu at the same time.

## Security

- Never commit `.env` files, API keys, private keys, Telegram tokens, or session strings.
- Use `.env.example` for placeholders only.
- Rotate any credential that was accidentally committed.
