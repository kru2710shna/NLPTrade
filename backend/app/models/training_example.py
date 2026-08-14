from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class TrainingExample(Base):
    __tablename__ = "training_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_id: Mapped[int | None] = mapped_column(ForeignKey("market_events.id"), nullable=True)

    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)

    source_type: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)

    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    previous_1d_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_5d_return: Mapped[float | None] = mapped_column(Float, nullable=True)

    return_1d: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_3d: Mapped[float | None] = mapped_column(Float, nullable=True)
    abnormal_return_1d: Mapped[float | None] = mapped_column(Float, nullable=True)

    label_1d: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)

    features_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
