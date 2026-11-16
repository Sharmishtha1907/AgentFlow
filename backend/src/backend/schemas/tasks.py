from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

#TASK
class TaskCreate(BaseModel):
    execution_id: uuid.UUID
    task_type: str
    description: str
    priority: int = 0
    max_retries: int

class Task(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    task_type: str
    description: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result_reference: str | None = None
    version: int

    model_config = ConfigDict(from_attributes=True)



class TaskStatusUpdate(BaseModel):
    new_status: str


class TaskResultUpdate(BaseModel):
    result_reference: str | None = None
    error_message: str | None = None

#TASK DEPENDENCY
class TaskDependencyCreate(BaseModel):
    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID


class TaskDependency(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID



#TASK ATTEMPT
class TaskAttemptCreate(BaseModel):
    task_id: uuid.UUID
    attempt_number: int
    worker_id: str | None


class TaskAttempt(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    attempt_number: int
    worker_id: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
        


