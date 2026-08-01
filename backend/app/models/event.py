from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class MarketEvent(Base):
    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
    )

    raw_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_documents.id"),
        nullable=True,
    )

    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(32), nullable=False)

    speaker: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
