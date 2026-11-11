import uuid

from sqlalchemy import (
    Index,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    func,
    CheckConstraint,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Task(Base):

    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            "retry_count >= 0",
            name="check_task_retry_count"
        ),
        CheckConstraint(
            "max_retries >= 0",
            name="check_task_max_retries"
        ),
        Index("ix_tasks_status_created_at", "status", "created_at"),
        Index("ix_tasks_execution_id", "execution_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    started_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    result_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    execution = relationship(
        "Execution",
        back_populates="tasks"
    )

    attempts = relationship(
        "TaskAttempt",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task"
    )