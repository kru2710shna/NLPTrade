from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    source_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    external_id: Mapped[str | None] = mapped_column(String(512), index=True, nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    ticker_context: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    company_context: Mapped[str | None] = mapped_column(String(255), nullable=True)

    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    raw_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    processing_status: Mapped[str] = mapped_column(
        String(32),
        default="new",
        server_default="new",
        index=True,
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
