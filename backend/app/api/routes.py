from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import desc

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.company import Company
from backend.app.models.price_bar import PriceBar
from backend.app.models.raw_document import RawDocument
from backend.app.models.event import MarketEvent


router = APIRouter(prefix="/api", tags=["NLPTrade API"])


def serialize_price_bar(bar: PriceBar) -> dict:
    return {
        "id": bar.id,
        "ticker": bar.ticker,
        "timestamp": bar.timestamp.isoformat() if bar.timestamp else None,
        "timeframe": bar.timeframe,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
        "trade_count": bar.trade_count,
        "vwap": bar.vwap,
        "source": bar.source,
    }


def serialize_raw_document(doc: RawDocument) -> dict:
    return {
        "id": doc.id,
        "source_type": doc.source_type,
        "source_name": doc.source_name,
        "url": doc.url,
        "title": doc.title,
        "published_at": doc.published_at.isoformat() if doc.published_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def serialize_market_event(event: MarketEvent) -> dict:
    return {
        "id": event.id,
        "ticker": event.ticker,
        "event_type": event.event_type,
        "sentiment": event.sentiment,
        "speaker": event.speaker,
        "quote": event.quote,
        "impact_score": event.impact_score,
        "confidence": event.confidence,
        "event_time": event.event_time.isoformat() if event.event_time else None,
    }


@router.get("/health")
def api_health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "ticker": settings.mvp_ticker,
    }


@router.get("/companies")
def get_companies() -> dict:
    db = SessionLocal()

    try:
        companies = db.query(Company).order_by(Company.ticker.asc()).all()

        return {
            "count": len(companies),
            "items": [
                {
                    "id": company.id,
                    "ticker": company.ticker,
                    "name": company.name,
                    "sector": company.sector,
                    "exchange": company.exchange,
                    "created_at": company.created_at.isoformat() if company.created_at else None,
                }
                for company in companies
            ],
        }

    finally:
        db.close()


@router.get("/price-bars/{ticker}")
def get_price_bars(
    ticker: str,
    limit: int = Query(default=30, ge=1, le=500),
) -> dict:
    db = SessionLocal()

    try:
        bars = (
            db.query(PriceBar)
            .filter(PriceBar.ticker == ticker.upper())
            .order_by(desc(PriceBar.timestamp))
            .limit(limit)
            .all()
        )

        # Return oldest → newest for frontend chart/table readability.
        bars = list(reversed(bars))

        return {
            "ticker": ticker.upper(),
            "count": len(bars),
            "items": [serialize_price_bar(bar) for bar in bars],
        }

    finally:
        db.close()


@router.get("/raw-documents")
def get_raw_documents(
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    db = SessionLocal()

    try:
        docs = (
            db.query(RawDocument)
            .order_by(desc(RawDocument.created_at))
            .limit(limit)
            .all()
        )

        return {
            "count": len(docs),
            "items": [serialize_raw_document(doc) for doc in docs],
        }

    finally:
        db.close()


@router.get("/market-events")
def get_market_events(
    ticker: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    db = SessionLocal()

    try:
        query = db.query(MarketEvent)

        if ticker:
            query = query.filter(MarketEvent.ticker == ticker.upper())

        events = query.order_by(desc(MarketEvent.event_time)).limit(limit).all()

        return {
            "count": len(events),
            "items": [serialize_market_event(event) for event in events],
        }

    finally:
        db.close()


@router.get("/dashboard/{ticker}")
def get_dashboard(
    ticker: str,
    price_limit: int = Query(default=30, ge=1, le=500),
) -> dict:
    db = SessionLocal()
    ticker = ticker.upper()

    try:
        company = db.query(Company).filter(Company.ticker == ticker).first()

        price_bars = (
            db.query(PriceBar)
            .filter(PriceBar.ticker == ticker)
            .order_by(desc(PriceBar.timestamp))
            .limit(price_limit)
            .all()
        )

        price_bars = list(reversed(price_bars))

        raw_documents_total = (
            db.query(RawDocument)
            .filter(RawDocument.ticker_context == ticker)
            .count()
        )

        market_events_total = (
            db.query(MarketEvent)
            .filter(MarketEvent.ticker == ticker)
            .count()
        )

        raw_documents = (
            db.query(RawDocument)
            .filter(RawDocument.ticker_context == ticker)
            .order_by(desc(RawDocument.created_at))
            .limit(10)
            .all()
        )

        market_events = (
            db.query(MarketEvent)
            .filter(MarketEvent.ticker == ticker)
            .order_by(desc(MarketEvent.event_time))
            .limit(10)
            .all()
        )

        latest_bar = price_bars[-1] if price_bars else None

        return {
            "ticker": ticker,
            "company": {
                "id": company.id if company else None,
                "ticker": company.ticker if company else ticker,
                "name": company.name if company else "Upcoming",
                "sector": company.sector if company else "Upcoming",
                "exchange": company.exchange if company else "Upcoming",
            },
            "latest_price": serialize_price_bar(latest_bar) if latest_bar else None,
            "price_bars": [serialize_price_bar(bar) for bar in price_bars],
            "raw_documents": [serialize_raw_document(doc) for doc in raw_documents],
            "market_events": [serialize_market_event(event) for event in market_events],
            "status": {
                "price_bars_count": len(price_bars),
                "raw_documents_count": raw_documents_total,
                "market_events_count": market_events_total,
            },
        }

    finally:
        db.close()
