
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from backend.database.models.outbox_event import OutboxEvent as OutboxEventModel
from backend.schemas import outbox_event as outbox_schema


def create_outbox_event(
    input: outbox_schema.OutboxEventCreate,
    db: Session
):
    """
    Create an outbox event inside the caller's transaction.

    IMPORTANT:
    This function does not commit.
    The caller is responsible for committing or rolling back.
    """

    event = OutboxEventModel(
        aggregate_type=input.aggregate_type,
        aggregate_id=input.aggregate_id,
        event_type=input.event_type,
        payload=input.payload,
        publish_attempts=0,
        
    )

    db.add(event)
    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)


def get_unpublished_events(
    limit: int,
    db: Session,
):
    """
    Fetch unpublished events for inspection or monitoring.

    Do not use this function as the publisher's claiming
    mechanism when multiple publishers are running.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    statement = (
        select(OutboxEventModel)
        .where(OutboxEventModel.published_at.is_(None))
        .order_by(OutboxEventModel.created_at.asc())
        .limit(limit)
    )

    events = db.scalars(statement).all()

    return [
        outbox_schema.OutboxEvent.model_validate(event)
        for event in events
    ]



def mark_event_as_published(
    event_id: uuid.UUID,
    db: Session
):
    """
    Mark an event as successfully published.

    Call this only after Kafka acknowledges the message.
    """

    event = db.get(OutboxEventModel, event_id)

    if not event:
        return None

    if event.published_at is None:
        event.published_at = datetime.now(timezone.utc)

    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)


def update_event_failure(
    event_id: uuid.UUID,
    db: Session
):
    """
    Increment the publishing attempt count after a failure.
    """

    event = db.get(OutboxEventModel, event_id)

    if not event:
        return None

    if event.published_at is not None:
        return event

    event.publish_attempts += 1

    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)



def get_outbox_event_by_id(
        event_id: uuid.UUID,
        db: Session
):
    event = db.get(OutboxEventModel, event_id)

    if event is None:
        return None

    return outbox_schema.OutboxEvent.model_validate(event)


def get_event_by_aggregate(
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        db: Session
):
    statement = (
        select(OutboxEventModel).where(
            OutboxEventModel.aggregate_type==aggregate_type,
            OutboxEventModel.aggregate_id==aggregate_id
        ).order_by(OutboxEventModel.created_at.asc())
    )

    events = db.scalars(statement).all()

    return [
        outbox_schema.OutboxEvent.model_validate(event)
        for event in events
    ]

def get_all_outbox_events(
    limit: int,
    offset: int,
    db: Session,
):
    """Fetch events with pagination for internal monitoring."""

    if limit <= 0 or offset < 0:
        raise ValueError("Invalid limit or offset")

    statement = (
        select(OutboxEventModel)
        .order_by(OutboxEventModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    events = db.scalars(statement).all()

    return [
        outbox_schema.OutboxEvent.model_validate(event)
        for event in events
    ]


def claim_unpublished_events(
    publisher_id: str,
    batch_size: int,
    lease_seconds: int,
    db: Session,
):
    """
    Atomically claim unpublished events for one publisher.

    The caller must commit this transaction before publishing
    the events to Kafka.
    """

    if not publisher_id:
        raise ValueError("publisher_id is required")

    if batch_size <= 0 or lease_seconds <= 0:
        raise ValueError("batch_size and lease_seconds must be positive")

    now = datetime.now(timezone.utc)
    lease_expiry = now + timedelta(seconds=lease_seconds)

    statement = (
        select(OutboxEventModel)
        .where(
            OutboxEventModel.published_at.is_(None),
            or_(
                OutboxEventModel.locked_until.is_(None),
                OutboxEventModel.locked_until < now,
            ),
        )
        .order_by(OutboxEventModel.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )

    events = db.scalars(statement).all()

    claimed_events = []

    for event in events:
        event.locked_by = publisher_id
        event.locked_until = lease_expiry

        claimed_events.append(
            outbox_schema.OutboxEvent.model_validate(event)
        )

    db.flush()

    return claimed_events


def mark_event_as_published(
    event_id: uuid.UUID,
    publisher_id: str,
    db: Session,
):
    """
    Mark an event as published after Kafka acknowledges it.

    Only the publisher holding the claim can mark it published.
    """

    statement=select(OutboxEventModel).where(OutboxEventModel.id == event_id).with_for_update()
    
    event = db.scalar(statement)
    
    if event is None:
        return None

    if event.published_at is not None:
        return outbox_schema.OutboxEvent.model_validate(event)

    if event.locked_by != publisher_id:
        raise ValueError("Publisher does not own this event claim")

    event.published_at = datetime.now(timezone.utc)
    event.locked_by = None
    event.locked_until = None
    event.last_error = None

    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)


def update_event_failure(
    event_id: uuid.UUID,
    publisher_id: str,
    error_message: str,
    db: Session,
):
    """
    Record a Kafka publishing failure.

    The lease is retained until it expires. This prevents
    an immediately failing event from being retried continuously.
    """

    statement=select(OutboxEventModel).where(OutboxEventModel.id == event_id).with_for_update()
    
    event = db.scalar(statement)

    if event is None:
        return None

    if event.published_at is not None:
        return outbox_schema.OutboxEvent.model_validate(event)

    if event.locked_by != publisher_id:
        raise ValueError("Publisher does not own this event claim")

    event.publish_attempts += 1
    event.last_error = error_message

    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)


def release_event_claim(
    event_id: uuid.UUID,
    publisher_id: str,
    db: Session,
):
    """
    Release an event claim without marking it published.

    Useful when a publisher is shutting down gracefully
    before attempting to publish the event.
    """

    statement=select(OutboxEventModel).where(OutboxEventModel.id == event_id).with_for_update()

    event = db.scalar(statement)

    if event is None:
        return None

    if event.published_at is not None:
        return outbox_schema.OutboxEvent.model_validate(event)

    if event.locked_by != publisher_id:
        raise ValueError("Publisher does not own this event claim")

    event.locked_by = None
    event.locked_until = None

    db.flush()

    return outbox_schema.OutboxEvent.model_validate(event)
