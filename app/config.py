from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app configuration. Values are loaded from environment variables
    / a .env file. See .env.example for the full list.
    """

    database_url: str = "postgresql://candyhub_user:candyhub_pass@localhost:5432/candyhub"

    secret_key: str = "change-this-to-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    first_admin_email: str = "admin@candyhub.gg"
    first_admin_password: str = "change-me-please"

    google_client_id: str = "1046278074092-cn7s7c09334ft03o2grqra7kg2vv2hs5.apps.googleusercontent.com"
    youtube_api_key: str = "AIzaSyAok3pU6LOlAvhJj31BSgAY0K5uJhM30kQ"
    youtube_channel_id: str = "UCJjHZ5rb_2LXfaRfJkFuetQ"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
