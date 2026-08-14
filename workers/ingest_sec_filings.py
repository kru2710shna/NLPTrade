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


def cik10(cik: str) -> str:
    return cik.replace("CIK", "").replace("-", "").zfill(10)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def document_exists(db, source_type: str, external_id: str) -> bool:
    return (
        db.query(RawDocument)
        .filter(RawDocument.source_type == source_type)
        .filter(RawDocument.external_id == external_id)
        .first()
        is not None
    )


def sec_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    clean_cik = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{clean_cik}/{accession_no_dashes}/{primary_document}"


def build_raw_text(
    filing: dict[str, Any],
    ticker: str,
    company: str,
    cik: str,
    url: str,
) -> str:
    parts = [
        "SOURCE_CONTEXT",
        f"ticker={ticker}",
        f"company={company}",
        f"cik={cik}",
        "",
        "SEC_FILING",
        f"form={filing.get('form') or ''}",
        f"accession_number={filing.get('accessionNumber') or ''}",
        f"filing_date={filing.get('filingDate') or ''}",
        f"report_date={filing.get('reportDate') or ''}",
        f"primary_document={filing.get('primaryDocument') or ''}",
        f"description={filing.get('primaryDocDescription') or ''}",
        f"url={url}",
    ]

    return "\n".join(parts).strip()


def fetch_recent_sec_filings(cik: str, limit: int) -> list[dict[str, Any]]:
    user_agent = settings.sec_user_agent

    if not user_agent:
        raise RuntimeError("Missing SEC_USER_AGENT in .env")

    padded_cik = cik10(cik)
    url = f"{settings.sec_data_base_url}/submissions/CIK{padded_cik}.json"

    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }

    with httpx.Client(timeout=30.0, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()

    recent = payload.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_documents = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    filings: list[dict[str, Any]] = []

    for index, form in enumerate(forms[:limit]):
        filings.append(
            {
                "form": form,
                "accessionNumber": accession_numbers[index] if index < len(accession_numbers) else None,
                "filingDate": filing_dates[index] if index < len(filing_dates) else None,
                "reportDate": report_dates[index] if index < len(report_dates) else None,
                "primaryDocument": primary_documents[index] if index < len(primary_documents) else None,
                "primaryDocDescription": descriptions[index] if index < len(descriptions) else None,
            }
        )

    return filings


def ingest_sec_filings(
    filings: list[dict[str, Any]],
    ticker: str,
    company: str,
    cik: str,
) -> None:
    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for filing in filings:
            accession_number = filing.get("accessionNumber")
            primary_document = filing.get("primaryDocument")

            if not accession_number or not primary_document:
                skipped += 1
                continue

            source_type = "sec_filing"
            external_id = f"{cik10(cik)}:{accession_number}"

            if document_exists(db, source_type=source_type, external_id=external_id):
                skipped += 1
                continue

            url = sec_document_url(
                cik=cik,
                accession_number=accession_number,
                primary_document=primary_document,
            )

            form = filing.get("form") or "SEC"
            filing_date = filing.get("filingDate") or ""
            title = f"{company} {form} filing {filing_date}".strip()

            doc = RawDocument(
                source_type=source_type,
                source_name="SEC EDGAR",
                external_id=external_id,
                query=f"CIK{cik10(cik)} recent filings",
                ticker_context=ticker,
                company_context=company,
                url=url,
                title=title,
                raw_text=build_raw_text(
                    filing=filing,
                    ticker=ticker,
                    company=company,
                    cik=cik10(cik),
                    url=url,
                ),
                raw_payload_json=filing,
                processing_status="new",
                published_at=parse_date(filing.get("filingDate")),
            )

            db.add(doc)
            inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"SEC ingestion complete. Inserted={inserted}, Skipped={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic SEC EDGAR recent filings ingestion worker.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. NVDA")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--cik", required=True, help="Company CIK, e.g. 0001045810")
    parser.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()

    ticker = args.ticker.upper()
    cik = cik10(args.cik)

    print(f"Fetching SEC filings for ticker={ticker} cik={cik} limit={args.limit}")

    filings = fetch_recent_sec_filings(
        cik=cik,
        limit=args.limit,
    )

    print(f"Fetched {len(filings)} filings.")

    ingest_sec_filings(
        filings=filings,
        ticker=ticker,
        company=args.company,
        cik=cik,
    )


if __name__ == "__main__":
    main()
