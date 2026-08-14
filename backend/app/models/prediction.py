from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_id: Mapped[int | None] = mapped_column(ForeignKey("market_events.id"), nullable=True)
    model_run_id: Mapped[int | None] = mapped_column(ForeignKey("model_runs.id"), nullable=True)

    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    horizon: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    prediction_label: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    prediction_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    evidence_strength: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uncertainty_level: Mapped[str | None] = mapped_column(String(32), nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
