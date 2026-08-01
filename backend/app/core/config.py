from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NLPTrade"
    env: str = "development"

    database_url: str = "postgresql+psycopg://krushna@localhost:5432/nlptrade_dev"

    # Market data
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_data_feed: str = "iex"
    alpha_vantage_api_key: str | None = None
    fmp_api_key: str | None = None
    marketstack_api_key: str | None = None

    # News / video / macro
    thenewsapi_key: str | None = None
    newsdata_api_key: str | None = None
    youtube_api_key: str | None = None
    fred_api_key: str | None = None
    congress_api_key: str | None = None

    # Infra
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
