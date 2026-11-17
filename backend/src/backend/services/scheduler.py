
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from backend.database.models import Task, TaskDependency, Execution
from backend.database.crud.outbox_event_crud import create_outbox_event
from backend.schemas import outbox_event as outbox_schema



#Read execution_id → Lock Execution → Lock Task → Evaluate dependencies → Update Task + Outbox → Commit
def evaluate_task_readiness(
    task_id: uuid.UUID,
    db: Session
):
    try:
        # 1. Read execution_id without acquiring a task lock.
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
        # Dependency creation/deletion must acquire this same lock.
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

        # 4. Ignore duplicate events and already-transitioned tasks.
        if task.status != "PENDING":
            result = {
                "task_id": str(task.id),
                "status": task.status,
                "message": "Task is not pending."
            }

            db.rollback()
            return result

        # 5. Retrieve prerequisite tasks.
        prerequisites = (
            db.query(Task)
            .join(
                TaskDependency,
                TaskDependency.depends_on_task_id == Task.id
            )
            .filter(TaskDependency.task_id == task.id)
            .all()
        )

        # 6. Evaluate prerequisite states.
        for prerequisite in prerequisites:

            if prerequisite.status == "FAILED":
                result = {
                    "task_id": str(task.id),
                    "status": "PENDING",
                    "message": "A prerequisite task has failed."
                }

                db.rollback()
                return result

            if prerequisite.status != "COMPLETED":
                result = {
                    "task_id": str(task.id),
                    "status": "PENDING",
                    "message": "Waiting for prerequisite tasks."
                }

                db.rollback()
                return result

        # 7. All prerequisites are completed.
        task.status = "READY"

        # 8. Create TASK_READY event in the same transaction.
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

        # 9. Commit state transition and outbox event atomically.
        db.commit()

        return {
            "task_id": str(task.id),
            "status": "READY",
            "message": "Task is ready for execution."
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate task readiness."
        ) from error
