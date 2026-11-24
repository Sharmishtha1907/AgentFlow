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



def fail_task(
    task_id: uuid.UUID,
    attempt_number: int,
    worker_id: str,
    error_message: str,
    db: Session
):
    try:
        # 1. Validate input
        if not worker_id or not worker_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Worker ID cannot be empty."
            )

        if not error_message or not error_message.strip():
            raise HTTPException(
                status_code=400,
                detail="Error message cannot be empty."
            )

        # 2. Lock task
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

        # 3. Validate task state
        if task.status != "RUNNING":
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot fail from status {task.status}."
            )

        # 4. Lock corresponding attempt
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

        # 5. Validate latest attempt
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

        # 6. Validate ownership and attempt state
        if attempt.worker_id != worker_id:
            raise HTTPException(
                status_code=403,
                detail="Worker does not own this task attempt."
            )

        if attempt.status != "RUNNING":
            raise HTTPException(
                status_code=409,
                detail=f"Attempt cannot fail from status {attempt.status}."
            )

        now = datetime.now(timezone.utc)

        # 7. Mark attempt as failed
        attempt.status = "FAILED"
        attempt.completed_at = now
        attempt.error_message = error_message.strip()

        # 8. Determine retry eligibility
        if task.retry_count < task.max_retries:

            task.retry_count += 1

            base_delay = 5
            max_delay = 60

            delay_seconds = min(
                base_delay * (2 ** task.retry_count),
                max_delay
            )

            next_retry_at = datetime.fromtimestamp(
                now.timestamp() + delay_seconds,
                tz=timezone.utc
            )

            task.status = "RETRY_WAIT"
            task.next_retry_at = next_retry_at
            task.error_message = error_message.strip()
            task.completed_at = None

            event_type = "TASK_RETRY_SCHEDULED"

        else:

            task.status = "FAILED"
            task.next_retry_at = None
            task.error_message = error_message.strip()
            task.completed_at = now

            event_type = "TASK_FAILED"

        # 9. Increment task version
        task.version += 1

        # 10. Create outbox event
        event_input = outbox_schema.OutboxEventCreate(
            aggregate_type="TASK",
            aggregate_id=task.id,
            event_type=event_type,
            payload={
                "task_id": str(task.id),
                "execution_id": str(task.execution_id),
                "attempt_number": attempt_number,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "error_message": error_message.strip(),
                "next_retry_at": (
                    task.next_retry_at.isoformat()
                    if task.next_retry_at
                    else None
                )
            }
        )

        create_outbox_event(
            input=event_input,
            db=db
        )

        # 11. Commit atomically
        db.commit()
        db.refresh(task)

        return {
            "task_id": task.id,
            "attempt_id": attempt.id,
            "attempt_number": attempt_number,
            "status": task.status,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "next_retry_at": task.next_retry_at,
            "worker_id": worker_id
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to record task failure."
        ) from error
