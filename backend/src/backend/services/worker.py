import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models import Task, Execution, TaskAttempt
from backend.database.crud.task_attempt_crud import create_attempt
from backend.database.crud.outbox_event_crud import create_outbox_event
from backend.schemas import task_attempt as task_attempt_schema
from backend.schemas import outbox_event as outbox_schema


def claim_task(
    task_id: uuid.UUID,
    worker_id: str,
    db: Session
):
    try:
        # 1. Find execution ID
        execution_id = (
            db.query(Task.execution_id)
            .filter(Task.id == task_id)
            .scalar()
        )

        if execution_id is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found."
            )

        # 2. Lock execution first
        execution = (
            db.query(Execution)
            .filter(Execution.id == execution_id)
            .with_for_update()
            .first()
        )

        if not execution:
            raise HTTPException(
                status_code=404,
                detail="Execution not found."
            )

        # 3. Lock task
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .with_for_update()
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found."
            )

        # 4. Validate task state
        if task.status != "READY":
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot be claimed from status {task.status}."
            )

        # 5. Allocate next attempt number
        last_attempt_number = (
            db.query(func.max(TaskAttempt.attempt_number))
            .filter(TaskAttempt.task_id == task.id)
            .scalar()
        )

        attempt_number = (last_attempt_number or 0) + 1

        # 6. Create attempt inside the current transaction
        attempt_input = task_attempt_schema.TaskAttemptCreate(
            task_id=task.id,
            attempt_number=attempt_number,
            worker_id=worker_id
        )

        create_attempt(
            input=attempt_input,
            db=db
        )

        # 7. Update task state
        task.status = "RUNNING"

        if task.started_at is None:
            task.started_at = datetime.now(timezone.utc)

        task.error_message = None
        task.version += 1

        # 8. Create outbox event
        event_input = outbox_schema.OutboxEventCreate(
            aggregate_type="TASK",
            aggregate_id=task.id,
            event_type="TASK_STARTED",
            payload={
                "task_id": str(task.id),
                "execution_id": str(task.execution_id),
                "attempt_number": attempt_number,
                "worker_id": worker_id
            }
        )

        create_outbox_event(
            input=event_input,
            db=db
        )

        # 9. Commit everything atomically
        db.commit()
        db.refresh(task)

        return {
            "task": task,
            "attempt_number": attempt_number,
            "worker_id": worker_id
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim task."
        ) from error