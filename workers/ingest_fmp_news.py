from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.raw_document import RawDocument


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    # FMP may return "2026-08-01 12:30:00" or ISO-like strings.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def document_exists(db, source_type: str, url: str | None, title: str | None) -> bool:
    query = db.query(RawDocument).filter(RawDocument.source_type == source_type)

    if url:
        return query.filter(RawDocument.url == url).first() is not None

    if title:
        return query.filter(RawDocument.title == title).first() is not None

    return False


def build_raw_text(
    article: dict[str, Any],
    ticker: str,
    company: str | None,
) -> str:
    parts = [
        "SOURCE_CONTEXT",
        f"ticker={ticker}",
        f"company={company or ''}",
        "",
        "FMP_STOCK_NEWS",
        f"title={article.get('title') or ''}",
        f"symbol={article.get('symbol') or ticker}",
        f"site={article.get('site') or ''}",
        f"publisher={article.get('publisher') or ''}",
        f"published_date={article.get('publishedDate') or article.get('date') or ''}",
        f"url={article.get('url') or ''}",
        f"text={article.get('text') or ''}",
    ]

    return "\n".join(parts).strip()


def fetch_fmp_news(
    ticker: str,
    limit: int,
) -> list[dict[str, Any]]:
    if not settings.fmp_api_key:
        raise RuntimeError("Missing FMP_API_KEY in .env")

    # Stable FMP stock-news endpoint.
    url = f"{settings.fmp_base_url}/news/stock"

    params: dict[str, Any] = {
        "symbols": ticker,
        "apikey": settings.fmp_api_key,
        "limit": limit,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)

        # Some plans/accounts may expose older v3 endpoint instead.
        if response.status_code == 404:
            fallback_url = "https://financialmodelingprep.com/api/v3/stock_news"
            fallback_params = {
                "tickers": ticker,
                "apikey": settings.fmp_api_key,
                "limit": limit,
            }
            response = client.get(fallback_url, params=fallback_params)

        response.raise_for_status()
        payload = response.json()

    if isinstance(payload, dict) and "data" in payload:
        data = payload["data"]
        return data if isinstance(data, list) else []

    return payload if isinstance(payload, list) else []


def ingest_fmp_news(
    articles: list[dict[str, Any]],
    ticker: str,
    company: str | None,
) -> None:
    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for article in articles:
            title = article.get("title")
            url = article.get("url")
            source_name = article.get("site") or article.get("publisher") or "FMP"
            published_at = parse_datetime(article.get("publishedDate") or article.get("date"))

            source_type = "fmp_stock_news"

            if document_exists(db, source_type=source_type, url=url, title=title):
                skipped += 1
                continue

            doc = RawDocument(
                source_type=source_type,
                source_name=str(source_name),
                url=url,
                title=title,
                raw_text=build_raw_text(
                    article=article,
                    ticker=ticker,
                    company=company,
                ),
                published_at=published_at,
            )

            db.add(doc)
            inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"FMP news ingestion complete. Inserted={inserted}, Skipped duplicates={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic FMP stock-news ingestion worker.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. NVDA")
    parser.add_argument("--company", default=None, help="Optional company context")
    parser.add_argument("--limit", type=int, default=50, help="Number of articles to fetch")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    print(f"Fetching FMP stock news for ticker={ticker!r} limit={args.limit}")

    articles = fetch_fmp_news(
        ticker=ticker,
        limit=args.limit,
    )

    print(f"Fetched {len(articles)} articles.")

    ingest_fmp_news(
        articles=articles,
        ticker=ticker,
        company=args.company,
    )


if __name__ == "__main__":
    main()
