from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal
from backend.app.models.company import Company
from backend.app.models.raw_document import RawDocument
from backend.app.models.event import MarketEvent


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def classify_huggingface_model(doc: RawDocument) -> dict:
    text = f"{doc.title or ''}\n{doc.raw_text or ''}\n{doc.query or ''}".lower()
    payload = doc.raw_payload_json or {}

    downloads = safe_int(payload.get("downloads"))
    likes = safe_int(payload.get("likes"))

    if any(term in text for term in ["tensorrt", "cuda", "triton", "h100", "h200", "gb200", "blackwell"]):
        event_type = "AI Infrastructure Ecosystem Signal"
    elif any(term in text for term in ["nvidia", "nemotron", "nemo"]):
        event_type = "AI Model Ecosystem Signal"
    else:
        event_type = "AI Developer Ecosystem Signal"

    if downloads >= 1000 or likes >= 20:
        sentiment = "bullish"
        impact_score = 0.46
        confidence = 0.64
        reason = "The Hugging Face artifact shows measurable developer/model ecosystem activity."
    else:
        sentiment = "neutral"
        impact_score = 0.28
        confidence = 0.58
        reason = "The Hugging Face artifact is relevant but has limited adoption signal."

    return {
        "event_type": event_type,
        "sentiment": sentiment,
        "impact_score": impact_score,
        "confidence": confidence,
        "reason": reason,
    }



def classify_sec_filing(doc: RawDocument) -> dict:
    text = f"{doc.title or ''}\n{doc.raw_text or ''}".lower()

    if "form=10-k" in text:
        return {
            "event_type": "Annual Report Filing",
            "sentiment": "neutral",
            "impact_score": 0.70,
            "confidence": 0.88,
            "reason": "The document is an official annual SEC filing.",
        }

    if "form=10-q" in text:
        return {
            "event_type": "Quarterly Report Filing",
            "sentiment": "neutral",
            "impact_score": 0.66,
            "confidence": 0.86,
            "reason": "The document is an official quarterly SEC filing.",
        }

    if "form=8-k" in text:
        return {
            "event_type": "Current Report Filing",
            "sentiment": "neutral",
            "impact_score": 0.62,
            "confidence": 0.84,
            "reason": "The document is an official current-report SEC filing.",
        }

    if "form=4" in text:
        return {
            "event_type": "Insider Transaction Filing",
            "sentiment": "neutral",
            "impact_score": 0.50,
            "confidence": 0.82,
            "reason": "The document is an official insider transaction filing.",
        }

    if "form=sc 13" in text or "form=13f" in text:
        return {
            "event_type": "Ownership Filing",
            "sentiment": "neutral",
            "impact_score": 0.52,
            "confidence": 0.80,
            "reason": "The document is an official ownership/institutional filing.",
        }

    return {
        "event_type": "SEC Filing",
        "sentiment": "neutral",
        "impact_score": 0.45,
        "confidence": 0.78,
        "reason": "The document is an official SEC filing.",
    }


def classify_news_document(doc: RawDocument) -> dict:
    text = f"{doc.title or ''}\n{doc.raw_text or ''}".lower()

    if any(term in text for term in ["vera rubin", "rubin platform", "blackwell", "gb200"]):
        return {
            "event_type": "Product Launch",
            "sentiment": "bullish",
            "impact_score": 0.78,
            "confidence": 0.80,
            "reason": "The document mentions NVIDIA product or platform momentum.",
        }

    if any(term in text for term in ["bull case", "buy rating", "upside", "top investors", "investors are buying", "buying nvidia"]):
        return {
            "event_type": "Investor Sentiment",
            "sentiment": "bullish",
            "impact_score": 0.62,
            "confidence": 0.72,
            "reason": "The document suggests positive investor or analyst sentiment.",
        }

    if any(term in text for term in ["whale trades", "unusual options", "options activity", "call options", "put options"]):
        return {
            "event_type": "Options Flow Signal",
            "sentiment": "neutral",
            "impact_score": 0.48,
            "confidence": 0.64,
            "reason": "The document discusses options or whale trading activity.",
        }

    if any(term in text for term in ["downgrade", "sell rating", "bear case", "export control", "china restriction", "margin pressure"]):
        return {
            "event_type": "Risk Signal",
            "sentiment": "bearish",
            "impact_score": 0.66,
            "confidence": 0.70,
            "reason": "The document contains negative or risk-related language.",
        }

    if any(term in text for term in ["earnings", "revenue", "guidance", "margin", "quarter", "profit"]):
        return {
            "event_type": "Financial Update",
            "sentiment": "neutral",
            "impact_score": 0.55,
            "confidence": 0.65,
            "reason": "The document discusses earnings or financial performance.",
        }

    return {
        "event_type": "General News",
        "sentiment": "neutral",
        "impact_score": 0.35,
        "confidence": 0.50,
        "reason": "No stronger news event rule matched.",
    }


def classify_event(doc: RawDocument) -> dict:
    if doc.source_type == "huggingface_model":
        return classify_huggingface_model(doc)

    if doc.source_type == "sec_filing":
        return classify_sec_filing(doc)

    return classify_news_document(doc)


def extract_quote(doc: RawDocument, reason: str) -> str:
    title = doc.title or "Untitled document"
    return f"{title} | Rule reason: {reason}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based raw document to market event extractor.")
    parser.add_argument("--ticker", required=True, help="Ticker to process, e.g. NVDA")
    parser.add_argument("--limit", type=int, default=300, help="Max raw documents to process")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess documents even if already processed")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        company = db.query(Company).filter(Company.ticker == ticker).first()

        if not company:
            raise RuntimeError(f"No company found for ticker={ticker}. Run seed script first.")

        query = db.query(RawDocument).filter(RawDocument.ticker_context == ticker)

        if not args.reprocess:
            query = query.filter(RawDocument.processing_status == "new")

        docs = (
            query
            .order_by(RawDocument.published_at.desc().nullslast(), RawDocument.created_at.desc())
            .limit(args.limit)
            .all()
        )

        print(f"Found {len(docs)} raw documents for ticker={ticker}")

        for doc in docs:
            existing_events = (
                db.query(MarketEvent)
                .filter(MarketEvent.raw_document_id == doc.id)
                .all()
            )

            if existing_events and not args.reprocess:
                doc.processing_status = "processed"
                doc.processed_at = datetime.now(timezone.utc)
                skipped += 1
                continue

            if existing_events and args.reprocess:
                for event in existing_events:
                    db.delete(event)
                db.flush()

            classification = classify_event(doc)
            quote = extract_quote(doc, classification["reason"])

            event = MarketEvent(
                company_id=company.id,
                raw_document_id=doc.id,
                ticker=ticker,
                event_type=classification["event_type"],
                sentiment=classification["sentiment"],
                speaker=None,
                quote=quote,
                impact_score=classification["impact_score"],
                confidence=classification["confidence"],
                event_time=doc.published_at or doc.created_at,
            )

            db.add(event)

            doc.processing_status = "processed"
            doc.processed_at = datetime.now(timezone.utc)

            inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"Rule extraction complete. Inserted events={inserted}, Skipped={skipped}")


if __name__ == "__main__":
    main()
