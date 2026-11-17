
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Execution(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    original_request: str
    status: str
    final_result: dict[str, Any] | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionCreate(BaseModel):
    user_id: uuid.UUID
    original_request: str = Field(min_length=1)


class ExecutionStatusUpdate(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=30
    )


class ExecutionFinalResultUpdate(BaseModel):
    final_result: dict[str, Any]
