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
    UniqueConstraint
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.database.base import Base
from sqlalchemy import ForeignKeyConstraint

class TaskResults(Base):

    __tablename__ = "task_results"

    __table_args__ = (
        ForeignKeyConstraint(
            ["task_id", "attempt_number"],
            [
                "task_attempts.task_id",
                "task_attempts.attempt_number"
            ],
            ondelete="CASCADE",
            name="fk_task_result_attempt"
        ),
        UniqueConstraint(
            "task_id",
            "attempt_number",
            name="uq_task_result_attempt"
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
        nullable=False,
        index=True
    )

    output_json:Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    output_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )
        
    task = relationship(
        "Task",
        back_populates="task_results"
    )

    