from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BOT_",
    )

    telegram_api_token: SecretStr
    amlbot_api_id: SecretStr
    amlbot_api_key: SecretStr
    otel_endpoint: str | None = None
    debug: bool = False
