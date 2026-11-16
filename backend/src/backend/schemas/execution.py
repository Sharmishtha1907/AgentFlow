from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Execution(BaseModel):
    id: uuid.UUID
    user_id: str
    original_request: str
    started_at: datetime | None

class ExecutionCreate(BaseModel):
    user_id: str
    original_request: str
    status: str
    final_result: dict|None
    started_at: datetime | None
    completed_at: datetime | None

