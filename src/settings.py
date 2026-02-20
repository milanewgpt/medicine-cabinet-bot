from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str
    telegram_webhook_secret: str = ""

    # Public URL (no trailing slash)
    public_base_url: str = "https://localhost"

    # AI provider
    ai_provider: str = "generic_http"  # generic_http | gemini | minimax
    ai_api_key: str = ""
    ai_base_url: str = "http://127.0.0.1:8080"
    ai_model: str = ""
    ai_timeout_seconds: int = 30
    ai_max_retries: int = 2

    # Google Sheets
    google_service_account_json: str = "service_account.json"
    google_sheet_id: str = ""
    google_sheet_tab_name: str = "Sheet1"

    # SSL (path to self-signed cert for Telegram webhook, empty = no custom cert)
    webhook_ssl_cert: str = ""

    # Misc
    timezone: str = "Asia/Jerusalem"

    @property
    def webhook_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/webhook"


settings = Settings()  # type: ignore[call-arg]
