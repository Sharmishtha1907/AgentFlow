import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models import Task, TaskAttempt
from backend.database.crud.task_attempt_crud import create_attempt
from backend.database.crud.outbox_event_crud import create_outbox_event
from backend.database.crud.task_result_crud import create_task_result
from backend.schemas import task_attempt as task_attempt_schema
from backend.schemas import outbox_event as outbox_schema
from backend.schemas import task_result as task_result_schema

def claim_task(
    task_id: uuid.UUID,
    worker_id: str,
    db: Session
):
    try:

        # 1. Lock task
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

        # 2. Validate task state
        if task.status != "READY":
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot be claimed from status {task.status}."
            )

        # 3. Allocate next attempt number
        last_attempt_number = (
            db.query(func.max(TaskAttempt.attempt_number))
            .filter(TaskAttempt.task_id == task.id)
            .scalar()
        )

        attempt_number = (last_attempt_number or 0) + 1

        # 4. Create attempt inside the current transaction
        attempt_input = task_attempt_schema.TaskAttemptCreate(
            task_id=task.id,
            attempt_number=attempt_number,
            worker_id=worker_id
        )

        create_attempt(
            input=attempt_input,
            db=db
        )

        # 5. Update task state
        task.status = "RUNNING"

        if task.started_at is None:
            task.started_at = datetime.now(timezone.utc)

        task.error_message = None
        task.version += 1

        if not worker_id or not worker_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Worker ID cannot be empty."
            )

        # 6. Create outbox event
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

        # 7. Commit everything atomically
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


def complete_task(
    task_id: uuid.UUID,
    attempt_number: int,
    worker_id: str,
    output_json: dict,
    db: Session
):
    try:

        # 1. Lock task
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

        if task.status != "RUNNING":
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot be completed from status {task.status}."
            )

        # 2. Lock the corresponding attempt
        attempt = (
            db.query(TaskAttempt)
            .filter(
                TaskAttempt.task_id == task_id,
                TaskAttempt.attempt_number == attempt_number
            )
            .with_for_update()
            .first()
        )

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Task attempt not found."
            )

        latest_attempt_number = (
        db.query(func.max(TaskAttempt.attempt_number))
        .filter(TaskAttempt.task_id == task.id)
        .scalar()
        )

        if attempt_number != latest_attempt_number:
            raise HTTPException(
                status_code=409,
                detail="This is not the latest task attempt."
            )

        if not worker_id or not worker_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Worker ID cannot be empty."
            )

        # 3. Validate attempt ownership and state
        if attempt.worker_id != worker_id:
            raise HTTPException(
                status_code=403,
                detail="Worker does not own this task attempt."
            )

        if attempt.status != "RUNNING":
            raise HTTPException(
                status_code=409,
                detail=f"Attempt cannot be completed from status {attempt.status}."
            )

        # 4. Create task result inside the current transaction
        result_input = task_result_schema.TaskResultCreate(
            task_id=task_id,
            attempt_number=attempt_number,
            output_json=output_json
        )

        result = create_task_result(
            input=result_input,
            db=db
        )

        # 5. Complete the attempt
        now = datetime.now(timezone.utc)

        attempt.status = "COMPLETED"
        attempt.completed_at = now
        attempt.error_message = None

        # 6. Complete the task
        task.status = "COMPLETED"
        task.completed_at = now
        task.error_message = None
        task.result_reference = str(result.id)
        task.version += 1

        # 7. Create completion event
        event_input = outbox_schema.OutboxEventCreate(
            aggregate_type="TASK",
            aggregate_id=task.id,
            event_type="TASK_COMPLETED",
            payload={
                "task_id": str(task.id),
                "execution_id": str(task.execution_id),
                "attempt_number": attempt_number,
                "result_id": str(result.id),
                "output_hash": result.output_hash
            }
        )

        create_outbox_event(
            input=event_input,
            db=db
        )

        # 8. Commit everything atomically
        db.commit()
        db.refresh(task)

        return {
            "task_id": task.id,
            "attempt_id": attempt.id,
            "result_id": result.id,
            "attempt_number": attempt_number,
            "status": task.status,
            "worker_id": worker_id
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete task."
        ) from error