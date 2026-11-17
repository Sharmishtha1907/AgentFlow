import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OutboxEventCreate(BaseModel):
    aggregate_type: str = Field(
        min_length=1,
        max_length=30
    )
    aggregate_id: uuid.UUID
    event_type: str = Field(
        min_length=1,
        max_length=100
    )
    payload: dict[str,Any]


class OutboxEvent(BaseModel):
    id: uuid.UUID
    aggregate_type: str
    aggregate_id: uuid.UUID
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
    published_at: datetime | None = None
    publish_attempts: int
    locked_by: str | None = None
    locked_until: datetime | None = None
    last_error: str | None = None

    model_config = ConfigDict(from_attributes=True)