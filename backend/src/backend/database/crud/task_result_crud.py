
import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from backend.database.models.task import Task
from backend.database.models.task_attempt import TaskAttempt
from backend.database.models.task_result import TaskResults
from backend.schemas import task_result as task_result_schema


# Generate SHA-256 hash for output
def calculate_output_hash(
    output_json: dict[str, Any] | None
) -> str | None:

    if output_json is None:
        return None

    serialized = json.dumps(
        output_json,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


# 1. CREATE TASK RESULT
def create_task_result(
    input: task_result_schema.TaskResultCreate,
    db: Session
):
    try:
        task = db.get(Task, input.task_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        attempt = db.scalar(
            select(TaskAttempt).where(
                TaskAttempt.task_id == input.task_id,
                TaskAttempt.attempt_number == input.attempt_number
            )
        )

        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Task attempt not found"
            )

        result = TaskResults(
            task_id=input.task_id,
            attempt_number=input.attempt_number,
            output_json=input.output_json,
            output_hash=calculate_output_hash(input.output_json)
        )

        db.add(result)
        db.flush()
        db.refresh(result)

        return task_result_schema.TaskResult.model_validate(result)

    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Result already exists for this attempt"
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="Database error while creating task result"
        ) from error
    
# 2. GET TASK RESULT BY ID
def get_task_result_by_id(
    result_id: UUID,
    db: Session
):
    try:
        result = db.get(TaskResults, result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Task result not found"
            )

        return task_result_schema.TaskResult.model_validate(result)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task result"
        )


# 3. GET ALL RESULTS FOR A TASK
def get_task_results_by_task(
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

        results = db.scalars(
            select(TaskResults)
            .where(TaskResults.task_id == task_id)
            .order_by(TaskResults.attempt_number.asc())
        ).all()

        return [
            task_result_schema.TaskResult.model_validate(result)
            for result in results
        ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task results"
        )


# 4. GET RESULT BY TASK AND ATTEMPT
def get_task_result_by_attempt(
    task_id: UUID,
    attempt_number: int,
    db: Session
):
    try:
        result = db.scalar(
            select(TaskResults).where(
                TaskResults.task_id == task_id,
                TaskResults.attempt_number == attempt_number
            )
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Task result not found for this attempt"
            )

        return task_result_schema.TaskResult.model_validate(result)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task result"
        )


# 5. GET ALL TASK RESULTS WITH PAGINATION
def get_all_task_results(
    offset: int,
    limit: int,
    db: Session
):
    try:
        results = db.scalars(
            select(TaskResults)
            .order_by(TaskResults.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        return [
            task_result_schema.TaskResult.model_validate(result)
            for result in results
        ]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching task results"
        )


# 6. UPDATE TASK RESULT
def update_task_result(
    result_id: UUID,
    output_json: dict[str, Any] | None,
    db: Session
):
    try:
        result = db.get(TaskResults, result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Task result not found"
            )

        result.output_json = output_json
        result.output_hash = calculate_output_hash(output_json)

        db.commit()
        db.refresh(result)

        return task_result_schema.TaskResult.model_validate(result)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while updating task result"
        )


# 7. DELETE TASK RESULT
def delete_task_result(
    result_id: UUID,
    db: Session
):
    try:
        result = db.get(TaskResults, result_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Task result not found"
            )

        db.delete(result)
        db.commit()

        return {
            "message": "Task result deleted successfully",
            "result_id": str(result_id)
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while deleting task result"
        )
