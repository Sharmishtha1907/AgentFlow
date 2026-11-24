import uuid

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class TaskAttempt(Base):

    __tablename__ = "task_attempts"

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "attempt_number",
            name="uq_task_attempt_number"
        ),
        CheckConstraint(
            "attempt_number >= 1",
            name="check_attempt_number_positive"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    worker_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RUNNING"
    )

    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    task = relationship(
        "Task",
        back_populates="attempts"
    )