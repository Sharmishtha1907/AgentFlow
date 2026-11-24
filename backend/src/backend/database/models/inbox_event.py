
import uuid

from sqlalchemy import (
    Index,
    String,
    DateTime,
    UniqueConstraint,
    func,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class InboxEvent(Base):

    __tablename__ = "inbox_events"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "consumer_name",
            name="uq_inbox_event_consumer"
        ),
        Index(
            "ix_inbox_consumer_processed_at",
            "consumer_name",
            "processed_at"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False
    )

    consumer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    processed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    
