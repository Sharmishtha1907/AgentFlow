
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, or_, insert
from sqlalchemy.orm import Session

from backend.database.models.inbox_event import InboxEvent as InboxEventModel
from backend.schemas import inbox_event as inbox_schema

def create_inbox_event(
    event_id: uuid.UUID,
    consumer_name: str,
    aggregate_id: uuid.UUID,
    event_type: str,
    db: Session
) -> bool:

    statement = (
        insert(InboxEventModel)
        .values(
            event_id=event_id,
            consumer_name=consumer_name,
            aggregate_id=aggregate_id,
            event_type=event_type
        )
        .on_conflict_do_nothing(
            constraint="uq_inbox_event_consumer"
        )
        .returning(InboxEventModel.id)
    )

    inserted_id = db.execute(statement).scalar_one_or_none()

    return inserted_id is not None


def is_event_processed(
    event_id: uuid.UUID,
    consumer_name: str,
    db: Session
) -> bool:

    statement = (
        select(InboxEventModel.id)
        .where(
            InboxEventModel.event_id == event_id,
            InboxEventModel.consumer_name == consumer_name
        )
        .limit(1)
    )

    return db.execute(statement).scalar_one_or_none() is not None