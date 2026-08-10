from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.price_bar import PriceBar


def parse_alpaca_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_alpaca_daily_bars(symbol: str, days: int = 60) -> list[dict]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    url = f"{settings.alpaca_base_url}/v2/stocks/bars"

    params = {
        "symbols": symbol,
        "timeframe": "1Day",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "feed": settings.alpaca_data_feed,
        "limit": 1000,
    }

    headers = {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
    }

    with httpx.Client(timeout=30.0, headers=headers) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    return data.get("bars", {}).get(symbol, [])


def upsert_price_bars(symbol: str, bars: list[dict]) -> None:
    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        for bar in bars:
            ts = parse_alpaca_time(bar["t"])

            existing = (
                db.query(PriceBar)
                .filter(
                    PriceBar.ticker == symbol,
                    PriceBar.timestamp == ts,
                    PriceBar.timeframe == "1Day",
                    PriceBar.source == "alpaca",
                )
                .first()
            )

            if existing:
                existing.open = bar["o"]
                existing.high = bar["h"]
                existing.low = bar["l"]
                existing.close = bar["c"]
                existing.volume = bar.get("v")
                existing.trade_count = bar.get("n")
                existing.vwap = bar.get("vw")
                updated += 1
            else:
                db.add(
                    PriceBar(
                        ticker=symbol,
                        timestamp=ts,
                        timeframe="1Day",
                        open=bar["o"],
                        high=bar["h"],
                        low=bar["l"],
                        close=bar["c"],
                        volume=bar.get("v"),
                        trade_count=bar.get("n"),
                        vwap=bar.get("vw"),
                        source="alpaca",
                    )
                )
                inserted += 1

        db.commit()

    finally:
        db.close()

    print(f"Inserted={inserted}, Updated={updated}")


def main() -> None:
    symbol = settings.mvp_ticker
    print(f"Fetching Alpaca daily bars for {symbol}...")

    bars = fetch_alpaca_daily_bars(symbol=symbol, days=60)

    print(f"Fetched {len(bars)} bars.")

    if not bars:
        print("No bars returned.")
        return

    upsert_price_bars(symbol=symbol, bars=bars)


if __name__ == "__main__":
    main()
