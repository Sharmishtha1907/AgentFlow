
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskResultCreate(BaseModel):
    task_id: uuid.UUID
    attempt_number: int
    output_json: dict[str, Any] | None = None


class TaskResult(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    attempt_number: int
    output_json: dict[str, Any] | None = None
    output_hash: str | None = None

    model_config = ConfigDict(from_attributes=True)
