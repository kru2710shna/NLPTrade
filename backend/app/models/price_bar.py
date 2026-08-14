from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class PriceBar(Base):
    __tablename__ = "price_bars"

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "timestamp",
            "timeframe",
            "source",
            name="uq_price_bars_ticker_timestamp_timeframe_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    timeframe: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    trade_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    vwap: Mapped[float | None] = mapped_column(Float, nullable=True)

    source: Mapped[str] = mapped_column(String(64), default="alpaca", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
