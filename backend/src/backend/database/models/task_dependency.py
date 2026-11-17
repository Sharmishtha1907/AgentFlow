import uuid

from sqlalchemy import ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class TaskDependency(Base):

    __tablename__ = "task_dependencies"

    __table_args__ = (
        CheckConstraint(
            "task_id != depends_on_task_id",
            name="check_no_self_dependency"
        ),
        UniqueConstraint(
        "task_id",
        "depends_on_task_id",
        name="uq_task_dependency"
        )
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

    depends_on_task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task = relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="dependencies"
    )

    depends_on_task = relationship(
        "Task",
        foreign_keys=[depends_on_task_id],
        back_populates="dependents"
    )