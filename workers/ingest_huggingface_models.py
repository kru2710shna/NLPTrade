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
    model: dict[str, Any],
    query: str,
    ticker: str | None,
    company: str | None,
) -> str:
    model_id = model.get("modelId") or model.get("id") or ""

    parts = [
        "SOURCE_CONTEXT",
        f"query={query}",
        f"ticker={ticker or ''}",
        f"company={company or ''}",
        "",
        "HUGGINGFACE_MODEL",
        f"model_id={model_id}",
        f"author={model.get('author') or ''}",
        f"pipeline_tag={model.get('pipeline_tag') or ''}",
        f"tags={model.get('tags') or []}",
        f"downloads={model.get('downloads') or 0}",
        f"likes={model.get('likes') or 0}",
        f"last_modified={model.get('lastModified') or ''}",
        f"url=https://huggingface.co/{model_id}",
    ]

    return "\n".join(parts).strip()


def fetch_huggingface_models(query: str, limit: int) -> list[dict[str, Any]]:
    if not settings.huggingface_api_key:
        raise RuntimeError("Missing HUGGINGFACE_API_KEY in .env")

    url = f"{settings.huggingface_base_url}/models"

    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
    }

    params = {
        "search": query,
        "limit": limit,
        "sort": "lastModified",
        "direction": -1,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()
        payload = response.json()

    return payload if isinstance(payload, list) else []


def ingest_models(
    models: list[dict[str, Any]],
    query: str,
    ticker: str | None,
    company: str | None,
) -> None:
    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for model in models:
            model_id = model.get("modelId") or model.get("id")

            if not model_id:
                skipped += 1
                continue

            url = f"https://huggingface.co/{model_id}"
            source_type = "huggingface_model"

            if document_exists(db, source_type=source_type, url=url, title=model_id):
                skipped += 1
                continue

            doc = RawDocument(
                source_type=source_type,
                source_name="Hugging Face Hub",
                external_id=str(model_id),
                query=query,
                ticker_context=ticker,
                company_context=company,
                url=url,
                title=str(model_id),
                raw_text=build_raw_text(
                    model=model,
                    query=query,
                    ticker=ticker,
                    company=company,
                ),
                raw_payload_json=model,
                processing_status="new",
                published_at=parse_datetime(model.get("lastModified")),
            )

            db.add(doc)
            inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"Hugging Face ingestion complete. Inserted={inserted}, Skipped duplicates={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic Hugging Face model ingestion worker.")
    parser.add_argument("--query", required=True, help='Search query, e.g. "nvidia"')
    parser.add_argument("--ticker", default=None)
    parser.add_argument("--company", default=None)
    parser.add_argument("--limit", type=int, default=25)

    args = parser.parse_args()

    print(f"Fetching Hugging Face models for query={args.query!r} limit={args.limit}")

    models = fetch_huggingface_models(
        query=args.query,
        limit=args.limit,
    )

    print(f"Fetched {len(models)} models.")

    ingest_models(
        models=models,
        query=args.query,
        ticker=args.ticker,
        company=args.company,
    )


if __name__ == "__main__":
    main()
