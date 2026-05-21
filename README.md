# Medicine Cabinet Telegram Bot

Intelligent Telegram bot for a family medicine cabinet. The bot does **NOT** diagnose or prescribe treatment — it only selects medicines from an existing Google Sheets inventory based on user-described symptoms.

> Russian-first project: the Telegram bot interface, symptom phrases, Google Sheet examples, and safety copy are intentionally designed for Russian-speaking users.

---

## Architecture

```
User (Telegram) → NGINX (SSL) → FastAPI webhook → python-telegram-bot v21+
                                                        │
                                        ┌───────────────┼───────────────┐
                                        ▼               ▼               ▼
                                   Voice → STT     NLU extraction    Google Sheet
                                   (AI provider)   (AI provider)     (gspread)
                                        │               │               │
                                        └───────┐       │       ┌───────┘
                                                ▼       ▼       ▼
                                           matcher.py (RapidFuzz scoring)
                                                        │
                                                        ▼
                                              safety.py (red flags,
                                              doctor-only classification)
                                                        │
                                                        ▼
                                              Formatted response → User
```

### Key design decisions

- **NLU never picks medicines** — it only converts free text to structured JSON.
- **Deterministic matcher** — RapidFuzz scoring against inventory data.
- **Provider-agnostic AI** — switch providers by changing env vars only.
- **No database** — sheet is the single source of truth, cached in memory (5 min TTL).
- **No medical data logging** — privacy by design.

---

## Project Structure

```
src/
  main.py              — FastAPI webhook server
  bot.py               — Telegram handlers
  sheets.py            — Google Sheets reader (with cache)
  nlu.py               — NLU orchestration (voice → text → JSON)
  matcher.py           — Symptom matching engine (RapidFuzz)
  safety.py            — Red flags + doctor-only logic
  models.py            — Pydantic models
  settings.py          — Env configuration (pydantic-settings)
  utils.py             — Russian text normalisation
  ai_client/
    __init__.py
    base.py            — Abstract AIClient interface
    factory.py         — Provider factory
    schemas.py         — NLU JSON schema + prompts
    providers/
      generic_http.py  — Any AI via HTTP (/transcribe, /extract)
      gemini.py        — Google Gemini (SDK + HTTP fallback)
      minimax.py       — MiniMax API
tests/
  conftest.py          — Shared fixtures
  test_matcher.py
  test_safety.py
  test_models.py
  test_utils.py
.env.example
requirements.txt
README.md
```

---

## Prerequisites

- Python 3.11+
- Telegram bot token (from @BotFather)
- Google service account with Sheets API
- An AI provider (any one of: self-hosted HTTP API, Gemini, MiniMax)
- VPS with Ubuntu 22.04+ (for production)

---

## 1. Create Telegram Bot

1. Open Telegram, find **@BotFather**.
2. Send `/newbot`, follow prompts.
3. Copy the token → `TELEGRAM_BOT_TOKEN`.
4. Generate a random webhook secret:
   ```bash
   openssl rand -hex 32
   ```
   → `TELEGRAM_WEBHOOK_SECRET`.

---

## 2. Google Service Account Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (or use existing).
3. Enable **Google Sheets API** and **Google Drive API**.
4. Go to **IAM & Admin → Service Accounts** → Create service account.
5. Create a key (JSON), download it → save as `service_account.json`.
6. Copy the service account email (e.g. `bot@project.iam.gserviceaccount.com`).

---

## 3. Google Sheet Setup

Create a Google Sheet with these exact column headers (first row):

| Название | Активное вещество | Форма | Для кого | Категория | Симптомы | Детям можно | Срок годности | Комментарий | Статус |
|---|---|---|---|---|---|---|---|---|---|
| Нурофен | ибупрофен | таблетки | взрослые | обезболивающее | головная боль, температура | Нет | 01.12.2027 | | Активен |
| Гексорал | гексэтидин | спрей | все | горло | боль в горле, ангина | Да | 01.10.2026 | | Активен |

**Rules:**
- `Статус` must be `Активен` for the medicine to be used.
- `Детям можно` = `Да` (exactly) means child-safe.
- `Срок годности` — formats: `DD.MM.YYYY`, `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/YYYY`.
- Add `ВРАЧ` anywhere in `Комментарий` to mark as doctor-only.
- Share the sheet with the service account email (Viewer access).

Copy the sheet ID from the URL:
```
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
```

---

## 4. AI Provider Configuration

### Option A: Generic HTTP (self-hosted / any AI)

Set `AI_PROVIDER=generic_http` and implement two endpoints:

#### POST /transcribe

Request: `multipart/form-data`, field `file` with audio bytes.

Response:
```json
{"text": "распознанный текст"}
```

#### POST /extract

Request:
```json
{
  "system": "system prompt...",
  "user": "user text...",
  "schema": { ... JSON schema ... },
  "model": "optional model name"
}
```

Response (must match NLU schema):
```json
{
  "person": "adult",
  "child_age": null,
  "symptoms_raw": "болит голова",
  "symptoms": ["головная боль"],
  "temperature_c": null,
  "duration_days": null,
  "red_flags": [],
  "intent": "what_to_take"
}
```

Env:
```env
AI_PROVIDER=generic_http
AI_BASE_URL=http://127.0.0.1:8080
AI_API_KEY=optional-bearer-token
```

### Option B: Google Gemini

```env
AI_PROVIDER=gemini
AI_API_KEY=your-gemini-api-key
AI_MODEL=gemini-1.5-flash
```

### Option C: MiniMax

```env
AI_PROVIDER=minimax
AI_API_KEY=your-minimax-key
AI_BASE_URL=https://api.minimax.chat
AI_MODEL=abab6.5s-chat
```

---

## 5. Local Development

```bash
# Clone
git clone <repo-url>
cd medicine-cabinet-bot

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\Activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your values

# Run tests
PYTHONPATH=. pytest tests/ -v

# Run locally (for testing with ngrok or similar)
PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8000
```

For local testing with Telegram webhook, use [ngrok](https://ngrok.com/):
```bash
ngrok http 8000
# Set PUBLIC_BASE_URL=https://xxxx.ngrok.io in .env
```

---

## 6. VPS Deployment (Ubuntu 22.04+)

Note: If you host multiple apps on one VPS, you may need to change the default `8000` port to avoid conflicts.
The `deploy/` templates use port `8001` as an example.

### 6.1 Server setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git
```

### 6.2 Deploy application

```bash
sudo mkdir -p /opt/medicine-bot
cd /opt/medicine-bot

# Upload or clone your code here
git clone <repo> .

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and edit configuration
cp .env.example .env
nano .env

# Copy service account JSON
# scp service_account.json user@server:/opt/medicine-bot/
```

### 6.3 SSL with Certbot

```bash
# Point your domain DNS A record to the server IP first
sudo certbot --nginx -d yourdomain.com
```

### 6.4 NGINX configuration

```bash
sudo nano /etc/nginx/sites-available/medicine-bot
```

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/medicine-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6.5 Systemd service

```bash
sudo nano /etc/systemd/system/medicine-bot.service
```

```ini
[Unit]
Description=Medicine Cabinet Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/medicine-bot
Environment=PYTHONPATH=/opt/medicine-bot
ExecStart=/opt/medicine-bot/.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /opt/medicine-bot
sudo systemctl daemon-reload
sudo systemctl enable medicine-bot
sudo systemctl start medicine-bot
sudo systemctl status medicine-bot
```

### 6.6 Verify

```bash
# Check health
curl https://yourdomain.com/health

# Check logs
sudo journalctl -u medicine-bot -f

# Check webhook is set
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## 7. Webhook Setup

The webhook is set automatically when the app starts (in `main.py` lifespan).

To manually set/reset:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourdomain.com/webhook&secret_token=<WEBHOOK_SECRET>"
```

---

## Testing Checklist

- [ ] **Voice works** — Send voice message, bot recognises and responds.
- [ ] **Sheet read works** — Bot finds medicines from the sheet.
- [ ] **Doctor-only works** — Antibiotics and `ВРАЧ`-comment medicines show warning.
- [ ] **Child filtering works** — Child query shows child-safe first, adult medicines with disclaimer.
- [ ] **Expired ignored** — Expired medicines are not shown.
- [ ] **Red flags work** — Dangerous symptoms trigger doctor/ambulance warning.
- [ ] **Inventory query** — "что есть от горла" returns sheet contents.
- [ ] **Unknown person** — Bot asks who is sick.
- [ ] `/start`, `/help`, `/inventory` commands respond correctly.

---

## Sample Conversations

**User:** `у ребёнка болит горло и температура`
**Bot:**
```
Можно рассмотреть (детям):
• Гексорал — боль в горле, ангина, фарингит
• Нурофен Детский — температура, боль, головная боль
```

**User:** `что есть от желудка`
**Bot:**
```
В аптечке есть:

Можно детям:
• Смекта — диарея, понос, тошнота, рвота, желудок
```

**User:** `ребёнок задыхается`
**Bot:**
```
⚠️ Лучше обратиться к врачу или вызвать скорую помощь.

(+ any mild relief suggestions if applicable)
```

---

## Security Notes

- No full medical text logged.
- No database — no data persistence.
- Webhook secret validates Telegram origin.
- Service account has read-only sheet access.
