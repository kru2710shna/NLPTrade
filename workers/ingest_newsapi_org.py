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
    query: str,
    ticker: str | None,
    company: str | None,
) -> str:
    source = article.get("source") or {}

    parts = [
        "SOURCE_CONTEXT",
        f"query={query}",
        f"ticker={ticker or ''}",
        f"company={company or ''}",
        "",
        "NEWSAPI_ORG_ARTICLE",
        f"title={article.get('title') or ''}",
        f"source={source.get('name') if isinstance(source, dict) else ''}",
        f"author={article.get('author') or ''}",
        f"description={article.get('description') or ''}",
        f"content={article.get('content') or ''}",
        f"url={article.get('url') or ''}",
        f"published_at={article.get('publishedAt') or ''}",
    ]

    return "\n".join(parts).strip()


def fetch_newsapi_articles(
    query: str,
    limit: int,
    language: str,
    from_date: str | None,
    sort_by: str,
) -> list[dict[str, Any]]:
    if not settings.newsapi_org_key:
        raise RuntimeError("Missing NEWSAPI_ORG_KEY in .env")

    url = f"{settings.newsapi_org_base_url}/everything"

    page_size = min(limit, 100)

    params: dict[str, Any] = {
        "q": query,
        "apiKey": settings.newsapi_org_key,
        "language": language,
        "pageSize": page_size,
        "sortBy": sort_by,
    }

    if from_date:
        params["from"] = from_date

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    return payload.get("articles", [])


def ingest_articles(
    articles: list[dict[str, Any]],
    query: str,
    ticker: str | None,
    company: str | None,
) -> None:
    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for article in articles:
            title = article.get("title")
            url = article.get("url")
            source = article.get("source") or {}

            if isinstance(source, dict):
                source_name = source.get("name") or "NewsAPI.org"
            else:
                source_name = "NewsAPI.org"

            source_type = "newsapi_org"

            if document_exists(db, source_type=source_type, url=url, title=title):
                skipped += 1
                continue

            doc = RawDocument(
                source_type=source_type,
                source_name=source_name,
                external_id=str(url or title or ""),
                query=query,
                ticker_context=ticker,
                company_context=company,
                url=url,
                title=title,
                raw_text=build_raw_text(
                    article=article,
                    query=query,
                    ticker=ticker,
                    company=company,
                ),
                raw_payload_json=article,
                processing_status="new",
                published_at=parse_datetime(article.get("publishedAt")),
            )

            db.add(doc)
            inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"NewsAPI.org ingestion complete. Inserted={inserted}, Skipped duplicates={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic NewsAPI.org ingestion worker.")
    parser.add_argument("--query", required=True, help='Search query, e.g. "NVIDIA OR NVDA"')
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--company", default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--language", default="en")
    parser.add_argument("--from-date", default=None, help="Optional date, e.g. 2026-01-01")
    parser.add_argument(
        "--sort-by",
        default="publishedAt",
        choices=["relevancy", "popularity", "publishedAt"],
    )

    args = parser.parse_args()

    print(f"Fetching NewsAPI.org articles for query={args.query!r} limit={args.limit}")

    articles = fetch_newsapi_articles(
        query=args.query,
        limit=args.limit,
        language=args.language,
        from_date=args.from_date,
        sort_by=args.sort_by,
    )

    print(f"Fetched {len(articles)} articles.")

    ingest_articles(
        articles=articles,
        query=args.query,
        ticker=args.ticker,
        company=args.company,
    )


if __name__ == "__main__":
    main()
