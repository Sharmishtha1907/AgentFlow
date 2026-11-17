
import uuid

from pydantic import BaseModel, ConfigDict


class TaskDependencyCreate(BaseModel):
    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID


class TaskDependency(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
