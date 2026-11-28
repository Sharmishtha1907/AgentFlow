import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from backend.database.crud.inbox_event_crud import create_inbox_event


CONSUMER_NAME = "agentflow-task-event-processor"


def process_event(event: dict, db: Session):
    """
    Processes a Kafka event using Inbox-based idempotency.

    The caller owns the database session.
    This function owns the transaction for this event.
    """

    try:
        # 1. Validate event envelope.
        required_fields = {
            "event_id",
            "aggregate_type",
            "aggregate_id",
            "event_type",
            "payload",
        }

        if not isinstance(event, dict):
            raise ValueError("Event must be a dictionary.")

        missing_fields = required_fields - event.keys()

        if missing_fields:
            raise ValueError(
                f"Missing event fields: {sorted(missing_fields)}"
            )

        # 2. Validate identifiers.
        event_id = uuid.UUID(event["event_id"])
        aggregate_id = uuid.UUID(event["aggregate_id"])

        if not isinstance(event["payload"], dict):
            raise ValueError("Event payload must be a dictionary.")

        # 3. Register event in Inbox.
        inserted = create_inbox_event(
            event_id=event_id,
            consumer_name=CONSUMER_NAME,
            aggregate_id=aggregate_id,
            event_type=event["event_type"],
            db=db,
        )

        # 4. Ignore duplicate events.
        if not inserted:
            db.rollback()
            return "DUPLICATE"

        # Event-specific processing will go here.

        db.commit()
        return "PROCESSED"

    except (ValueError, TypeError):
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()
        raise RuntimeError(
            "Database error while processing Kafka event."
        ) from error

    except Exception:
        db.rollback()
        raise