
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.models.task import Task
from backend.database.models.task_attempt import TaskAttempt as TaskAttemptModel
from backend.schemas import task_attempt as task_attempt_schema


def create_attempt(
    input: task_attempt_schema.TaskAttemptCreate,
    db: Session
):
    try:
        task = db.get(Task, input.task_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        attempt = TaskAttemptModel(
            task_id=input.task_id,
            attempt_number=input.attempt_number,
            worker_id=input.worker_id,
            status="RUNNING"
        )

        db.add(attempt)
        db.flush()
        db.refresh(attempt)

        return task_attempt_schema.TaskAttempt.model_validate(attempt)

    except HTTPException:
        raise

    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Attempt number already exists for this task"
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="Database error while creating task attempt"
        ) from error

def get_attempt_by_id(
    attempt_id: UUID,
    db: Session
):
    try:
        attempt = db.get(TaskAttemptModel, attempt_id)

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Task attempt not found"
            )

        return task_attempt_schema.TaskAttempt.model_validate(attempt)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task attempt"
        )


def get_attempts_by_task(
    task_id: UUID,
    db: Session
):
    try:
        task = db.get(Task, task_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        attempts = db.scalars(
            select(TaskAttemptModel)
            .where(TaskAttemptModel.task_id == task_id)
            .order_by(TaskAttemptModel.attempt_number.asc())
        ).all()

        return [
            task_attempt_schema.TaskAttempt.model_validate(attempt)
            for attempt in attempts
        ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task attempts"
        )


def get_all_attempts(
    offset: int,
    limit: int,
    db: Session
):
    try:
        attempts = db.scalars(
            select(TaskAttemptModel)
            .order_by(TaskAttemptModel.started_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            task_attempt_schema.TaskAttempt.model_validate(attempt)
            for attempt in attempts
        ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task attempts"
        )


def update_attempt_status(
    attempt_id: UUID,
    new_status: str,
    error_message: str | None,
    db: Session
):
    try:
        allowed_statuses = {"COMPLETED", "FAILED"}

        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Attempt status must be COMPLETED or FAILED"
            )

        attempt = db.get(TaskAttemptModel, attempt_id)

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Task attempt not found"
            )

        if attempt.status != "RUNNING":
            raise HTTPException(
                status_code=409,
                detail="Only running attempts can be completed"
            )

        attempt.status = new_status
        attempt.error_message = error_message
        attempt.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(attempt)

        return task_attempt_schema.TaskAttempt.model_validate(attempt)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while updating task attempt"
        )
