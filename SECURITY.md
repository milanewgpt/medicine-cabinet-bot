# Security Policy

## Scope

This project is a household medicine inventory assistant. It is health-adjacent and may process sensitive family information through Telegram messages and the configured inventory backend.

## Supported version

The current public repository represents the working MVP. Security fixes should target the default branch.

## Reporting a vulnerability

Please open a private security advisory on GitHub if available, or contact the repository owner directly.

Do not post real Telegram tokens, API keys, service account JSON, private inventory links, or family health data in public issues.

## Secrets

Never commit:

- `.env` files;
- Telegram bot tokens;
- webhook secrets;
- AI provider API keys;
- Google service account JSON files;
- private medicine inventory data;
- logs containing user health text or chat IDs.

Use `.env.example` for placeholders only.

## Runtime security notes

- `TELEGRAM_WEBHOOK_SECRET` should be configured in production.
- `PUBLIC_BASE_URL` should point to the production deployment URL.
- Google service account access should be limited to the specific medicine inventory sheet.
- Hosting platform environment variables should be used for all secrets.
- Logs should avoid storing raw user health messages unless explicitly needed for debugging and protected accordingly.

## Medical safety notes

Security for this project includes product safety:

- no diagnosis;
- no prescription;
- no dosage instructions;
- filter expired medicines;
- separate adult/child suitability;
- escalate red flags to medical care.

See `docs/safety-model.md`.
