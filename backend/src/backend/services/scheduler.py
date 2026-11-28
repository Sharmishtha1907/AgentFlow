
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from sqlalchemy import func
from backend.database.models import Task, TaskDependency, Execution
from backend.database.crud.outbox_event_crud import create_outbox_event
from backend.schemas import outbox_event as outbox_schema



#Read execution_id → Lock Execution → Lock Task → Evaluate dependencies → Update Task + Outbox → Commit

def evaluate_task_readiness(
    task_id: uuid.UUID,
    db: Session
):
    try:
        result = evaluate_task_readiness_in_transaction(
            task_id=task_id,
            db=db
        )

        db.commit()
        return result

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate task readiness."
        ) from error


def evaluate_task_readiness_in_transaction(
    task_id: uuid.UUID,
    db: Session
):
    """
    Evaluates task readiness inside the caller's transaction.

    Does not commit or rollback.
    The caller is responsible for transaction ownership.
    """
    # 1. Read execution ID.
    execution_id = (
        db.query(Task.execution_id)
        .filter(Task.id == task_id)
        .scalar()
    )

    if execution_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    # 2. Lock Execution first.
    execution = (
        db.query(Execution)
        .filter(Execution.id == execution_id)
        .with_for_update()
        .first()
    )

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found."
        )

    # 3. Lock Task second.
    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .with_for_update()
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    # 4. Ignore already-transitioned tasks.
    if task.status != "PENDING":
        return {
            "task_id": str(task.id),
            "status": task.status,
            "message": "Task is not pending."
        }

    # 5. Retrieve prerequisites.
    prerequisites = (
        db.query(Task)
        .join(
            TaskDependency,
            TaskDependency.depends_on_task_id == Task.id
        )
        .filter(TaskDependency.task_id == task.id)
        .all()
    )

    # 6. Check prerequisite states.
    for prerequisite in prerequisites:

        if prerequisite.status == "FAILED":
            return {
                "task_id": str(task.id),
                "status": "PENDING",
                "message": "A prerequisite task has failed."
            }

        if prerequisite.status != "COMPLETED":
            return {
                "task_id": str(task.id),
                "status": "PENDING",
                "message": "Waiting for prerequisite tasks."
            }

    # 7. All prerequisites completed.
    task.status = "READY"
    task.version += 1

    # 8. Create outbox event.
    event_input = outbox_schema.OutboxEventCreate(
        aggregate_type="TASK",
        aggregate_id=task.id,
        event_type="TASK_READY",
        payload={
            "task_id": str(task.id),
            "execution_id": str(task.execution_id),
            "task_type": task.task_type,
            "description": task.description,
            "priority": task.priority,
        }
    )

    create_outbox_event(
        input=event_input,
        db=db
    )

    return {
        "task_id": str(task.id),
        "status": "READY",
        "message": "Task is ready for execution."
    }



def promote_due_retries(batch_size: int, db: Session):
    try:
        if batch_size < 1:
            raise HTTPException(
                status_code=400,
                detail="Batch size must be at least 1."
            )

        tasks = (
            db.query(Task)
            .filter(
                Task.status == "RETRY_WAIT",
                Task.next_retry_at <= func.now()
            )
            .order_by(
                Task.next_retry_at.asc(),
                Task.priority.desc()
            )
            .with_for_update(skip_locked=True)
            .limit(batch_size)
            .all()
        )

        promoted_count = 0

        for task in tasks:
            task.status = "READY"
            task.next_retry_at = None
            task.version += 1

            event_input = outbox_schema.OutboxEventCreate(
                aggregate_type="TASK",
                aggregate_id=task.id,
                event_type="TASK_READY",
                payload={
                    "task_id": str(task.id),
                    "execution_id": str(task.execution_id),
                    "task_type": task.task_type,
                    "description": task.description,
                    "priority": task.priority,
                    "retry_count": task.retry_count
                }
            )

            create_outbox_event(
                input=event_input,
                db=db
            )

            promoted_count += 1

        db.commit()

        return {
            "promoted_count": promoted_count,
            "message": f"Promoted {promoted_count} due retries."
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to promote due retries."
        ) from error
