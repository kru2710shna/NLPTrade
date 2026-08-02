from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta, timezone
import httpx
from backend.app.core.config import settings

TIMEOUT = 20.0


def ok(name: str, detail: str = "") -> None:
    print(f"{name} OK {detail}")


def fail(name: str, error: Exception | str) -> None:
    print(f"{name} FAILED: {error}")


def test_sec_edgar() -> None:
    name = "SEC EDGAR"

    url = f"{settings.sec_data_base_url}/submissions/CIK{settings.mvp_company_cik}.json"
    headers = {
        "User-Agent": settings.sec_user_agent,
        "Accept-Encoding": "gzip, deflate",
    }

    try:
        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()

        company_name = data.get("name")
        cik = data.get("cik")
        filings_count = len(data.get("filings", {}).get("recent", {}).get("accessionNumber", []))

        ok(name, f"name={company_name}, cik={cik}, recent_filings={filings_count}")

    except Exception as e:
        fail(name, e)


def test_fmp() -> None:
    name = "FMP"

    if not settings.fmp_api_key:
        fail(name, "missing FMP_API_KEY")
        return

    # FMP stable endpoint style.
    url = f"{settings.fmp_base_url}/profile"
    params = {
        "symbol": settings.mvp_ticker,
        "apikey": settings.fmp_api_key,
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        if not data:
            fail(name, "empty response")
            return

        first = data[0] if isinstance(data, list) else data
        ok(name, f"symbol={first.get('symbol')}, company={first.get('companyName') or first.get('companyName')}")

    except Exception as e:
        fail(name, e)


def test_newsapi_org() -> None:
    name = "NewsAPI.org"

    if not settings.newsapi_org_key:
        fail(name, "missing NEWSAPI_ORG_KEY")
        return

    url = f"{settings.newsapi_org_base_url}/everything"
    params = {
        "q": settings.mvp_ticker,
        "pageSize": 1,
        "sortBy": "publishedAt",
        "apiKey": settings.newsapi_org_key,
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        total = data.get("totalResults")
        articles = data.get("articles", [])
        title = articles[0].get("title") if articles else "no article returned"

        ok(name, f"totalResults={total}, sample_title={title}")

    except Exception as e:
        fail(name, e)


def test_fred() -> None:
    name = "FRED"

    if not settings.fred_api_key:
        fail(name, "missing FRED_API_KEY")
        return

    url = f"{settings.fred_base_url}/series/observations"
    params = {
        "series_id": "DGS10",
        "api_key": settings.fred_api_key,
        "file_type": "json",
        "limit": 1,
        "sort_order": "desc",
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        obs = data.get("observations", [])
        if not obs:
            fail(name, "empty observations")
            return

        latest = obs[0]
        ok(name, f"DGS10 date={latest.get('date')}, value={latest.get('value')}")

    except Exception as e:
        fail(name, e)


def test_alpaca_market_data() -> None:
    name = "Alpaca Market Data"

    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        fail(name, "missing ALPACA_API_KEY or ALPACA_SECRET_KEY")
        return

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=14)

    url = f"{settings.alpaca_base_url}/v2/stocks/bars"
    params = {
        "symbols": settings.mvp_ticker,
        "timeframe": "1Day",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "feed": settings.alpaca_data_feed,
        "limit": 5,
    }

    headers = {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
    }

    try:
        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        bars = data.get("bars", {}).get(settings.mvp_ticker, [])
        if not bars:
            fail(name, f"no bars returned; response={data}")
            return

        latest = bars[-1]
        ok(name, f"latest_bar_time={latest.get('t')}, close={latest.get('c')}")

    except Exception as e:
        fail(name, e)


def main() -> None:
    print("Checking API connections for NLPTrade...")
    print(f"Ticker: {settings.mvp_ticker}")
    print("-" * 80)

    test_sec_edgar()
    test_fmp()
    test_newsapi_org()
    test_fred()
    test_alpaca_market_data()

    print("-" * 80)
    print("Done.")


if __name__ == "__main__":
    main()
