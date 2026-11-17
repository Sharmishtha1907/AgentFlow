import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskAttemptCreate(BaseModel):
    task_id: uuid.UUID
    attempt_number: int
    worker_id: str | None = None


class TaskAttempt(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    attempt_number: int
    worker_id: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)