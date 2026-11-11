import uuid

from sqlalchemy import (
    Index,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base



class OutboxEvent(Base):

    __table_args__ = (
        Index("ix_outbox_events_published_at", "published_at"),
    )

    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    published_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    publish_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0  
    )