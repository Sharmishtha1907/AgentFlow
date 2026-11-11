import uuid

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    func,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.database.base import Base

class ExecutionResults(Base):

    __tablename__ = "execution_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("executions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    result_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    execution = relationship(
        "Execution",
        back_populates="execution_results"
    )
