from __future__ import annotations

import argparse
from bisect import bisect_left
from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal
from backend.app.models.event import MarketEvent
from backend.app.models.price_bar import PriceBar
from backend.app.models.raw_document import RawDocument
from backend.app.models.training_example import TrainingExample


BULLISH_THRESHOLD = 0.0075
BEARISH_THRESHOLD = -0.0075


def pct_return(new_price: float, old_price: float) -> float | None:
    if old_price == 0:
        return None

    return (new_price - old_price) / old_price


def label_from_return(value: float | None) -> str | None:
    if value is None:
        return None

    if value > BULLISH_THRESHOLD:
        return "bullish"

    if value < BEARISH_THRESHOLD:
        return "bearish"

    return "neutral"


def bar_date(bar: PriceBar) -> date:
    return bar.timestamp.date()


def existing_training_example(db, event_id: int) -> bool:
    return (
        db.query(TrainingExample)
        .filter(TrainingExample.event_id == event_id)
        .first()
        is not None
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ML training examples from events and price bars.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. NVDA")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--rebuild", action="store_true", help="Delete existing examples for ticker first")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    db = SessionLocal()

    created = 0
    skipped_existing = 0
    skipped_no_event_time = 0
    skipped_no_price_window = 0

    try:
        if args.rebuild:
            deleted = (
                db.query(TrainingExample)
                .filter(TrainingExample.ticker == ticker)
                .delete()
            )
            db.commit()
            print(f"Deleted existing training examples: {deleted}")

        bars = (
            db.query(PriceBar)
            .filter(PriceBar.ticker == ticker)
            .order_by(PriceBar.timestamp.asc())
            .all()
        )

        bars = [bar for bar in bars if bar.close is not None]

        if len(bars) < 8:
            raise RuntimeError(f"Not enough price bars for ticker={ticker}. Found {len(bars)}")

        dates = [bar_date(bar) for bar in bars]

        events = (
            db.query(MarketEvent)
            .filter(MarketEvent.ticker == ticker)
            .order_by(MarketEvent.event_time.asc().nullslast())
            .limit(args.limit)
            .all()
        )

        print(f"Found events={len(events)} price_bars={len(bars)} for ticker={ticker}")

        for event in events:
            if event.id is None:
                continue

            if existing_training_example(db, event.id):
                skipped_existing += 1
                continue

            if not event.event_time:
                skipped_no_event_time += 1
                continue

            event_date = event.event_time.date()

            # First available bar on or after event date.
            idx = bisect_left(dates, event_date)

            # Need previous 5 bars and next 3 bars.
            if idx < 5 or idx + 3 >= len(bars):
                skipped_no_price_window += 1
                continue

            event_bar = bars[idx]
            prev_1_bar = bars[idx - 1]
            prev_5_bar = bars[idx - 5]
            next_1_bar = bars[idx + 1]
            next_3_bar = bars[idx + 3]

            previous_1d_return = pct_return(event_bar.close, prev_1_bar.close)
            previous_5d_return = pct_return(event_bar.close, prev_5_bar.close)

            return_1d = pct_return(next_1_bar.close, event_bar.close)
            return_3d = pct_return(next_3_bar.close, event_bar.close)

            # For now abnormal return = raw return.
            # Later we subtract QQQ/SOXX benchmark return.
            abnormal_return_1d = return_1d
            label_1d = label_from_return(abnormal_return_1d)

            doc = None
            if event.raw_document_id:
                doc = (
                    db.query(RawDocument)
                    .filter(RawDocument.id == event.raw_document_id)
                    .first()
                )

            example = TrainingExample(
                event_id=event.id,
                ticker=ticker,
                event_time=event.event_time,
                source_type=doc.source_type if doc else None,
                event_type=event.event_type,
                sentiment=event.sentiment,
                sentiment_score=None,
                impact_score=event.impact_score,
                confidence=event.confidence,
                previous_1d_return=previous_1d_return,
                previous_5d_return=previous_5d_return,
                return_1d=return_1d,
                return_3d=return_3d,
                abnormal_return_1d=abnormal_return_1d,
                label_1d=label_1d,
                features_json={
                    "source_name": doc.source_name if doc else None,
                    "source_type": doc.source_type if doc else None,
                    "event_type": event.event_type,
                    "sentiment": event.sentiment,
                    "impact_score": event.impact_score,
                    "confidence": event.confidence,
                    "event_bar_date": str(bar_date(event_bar)),
                    "event_bar_close": event_bar.close,
                    "next_1_bar_date": str(bar_date(next_1_bar)),
                    "next_1_bar_close": next_1_bar.close,
                    "next_3_bar_date": str(bar_date(next_3_bar)),
                    "next_3_bar_close": next_3_bar.close,
                },
            )

            db.add(example)
            created += 1

        db.commit()

    finally:
        db.close()

    print("Training example creation complete.")
    print(f"Created={created}")
    print(f"Skipped existing={skipped_existing}")
    print(f"Skipped no event_time={skipped_no_event_time}")
    print(f"Skipped missing price window={skipped_no_price_window}")


if __name__ == "__main__":
    main()
