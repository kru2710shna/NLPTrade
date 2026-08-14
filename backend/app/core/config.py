from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "NLPTrade"
    env: str = "development"

    # Database / infra
    database_url: str = "postgresql+psycopg://krushna@localhost:5432/nlptrade_dev"
    redis_url: str = "redis://localhost:6379/0"

    # MVP company
    mvp_ticker: str = "NVDA"
    mvp_company_name: str = "NVIDIA Corporation"
    mvp_company_cik: str = "0001045810"
    mvp_exchange: str = "NASDAQ"

    # Market data
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_data_feed: str = "iex"
    alpaca_base_url: str = "https://data.alpaca.markets"

    alpha_vantage_api_key: str | None = None
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"

    fmp_api_key: str | None = None
    fmp_base_url: str = "https://financialmodelingprep.com/stable"

    marketstack_api_key: str | None = None
    marketstack_base_url: str = "http://api.marketstack.com/v1"

    # News
    newsapi_org_key: str | None = None
    newsapi_org_base_url: str = "https://newsapi.org/v2"

    thenewsapi_key: str | None = None
    thenewsapi_base_url: str = "https://api.thenewsapi.com/v1/news"

    newsdata_api_key: str | None = None
    newsdata_base_url: str = "https://newsdata.io/api/1"

    gdelt_doc_base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"

    # SEC / filings
    sec_api_key: str | None = None
    sec_user_agent: str = "NLPTrade/0.1 contact-email"
    sec_data_base_url: str = "https://data.sec.gov"
    sec_archives_base_url: str = "https://www.sec.gov/Archives"
    sec_company_tickers_url: str = "https://www.sec.gov/files/company_tickers_exchange.json"

    # Macro / government
    fred_api_key: str | None = None
    fred_base_url: str = "https://api.stlouisfed.org/fred"

    congress_api_key: str | None = None
    congress_base_url: str = "https://api.congress.gov/v3"

    govinfo_api_key: str | None = None
    govinfo_base_url: str = "https://api.govinfo.gov"

    # Video / speech
    youtube_api_key: str | None = None
    youtube_base_url: str = "https://www.googleapis.com/youtube/v3"

    assemblyai_api_key: str | None = None
    assemblyai_base_url: str = "https://api.assemblyai.com/v2"

    # AI ecosystem / model hub
    huggingface_api_key: str | None = None
    huggingface_base_url: str = "https://huggingface.co/api"

    # Social
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "NLPTrade/0.1"

    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None


settings = Settings()
