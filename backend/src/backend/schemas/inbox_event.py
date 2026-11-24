import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class InboxEventCreate(BaseModel):
    event_id: uuid.UUID
    consumer_name: str
    aggregate_id: uuid.UUID
    event_type: str
    

class InboxEvent(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    consumer_name: str
    aggregate_id: uuid.UUID
    event_type: str
    created_at: datetime
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)