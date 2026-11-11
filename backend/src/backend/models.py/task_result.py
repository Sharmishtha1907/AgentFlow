import uuid

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    func,
    CheckConstraint,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.database.base import Base

class TaskResults(Base):

    __tablename__ = "task_results"

    __table_args__ = (
        CheckConstraint(
            "retry_count >= 0",
            name="check_task_retry_count"
        ),
        CheckConstraint(
            "max_retries >= 0",
            name="check_task_max_retries"
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
        ForeignKey("attempts.attempt_number"),
        nullable=False,
        index=True
    )

    output_json:Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    output__hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )
        
    task = relationship(
        "Task",
        back_populates="task_results"
    )

    attempts = relationship(
        "TaskAttempt",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    