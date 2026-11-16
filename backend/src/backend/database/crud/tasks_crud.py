from backend.database.session import get_db
from backend.schemas import tasks
from requests import Session
from backend.database.models import Task, Execution
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


def create_task(
    input: tasks.TaskCreate,
    db: Session
):
    try:
        t = Task(
            execution_id=input.execution_id,
            task_type=input.original_request,
            status="PENDING",
            priority= 1,
            retry_count= 0,
            max_retries= 3  
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        
        return tasks.Task.model_validate(t)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task due to a database error."
        )


def get_task_by_id(
    task_id: uuid.UUID,
    db: Session
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        return tasks.Task.model_validate(task)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task due to a database error."
        )


def get_tasks_by_execution(
    execution_id: uuid.UUID,
    db: Session,
    offset: int = 0,
    limit: int = 20
):
    try:
        execution = db.get(Execution, execution_id)

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found."
            )

        task_list = (
            db.query(Task)
            .filter(Task.execution_id == execution_id)
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            tasks.Task.model_validate(task)
            for task in task_list
        ]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks for this execution."
        )



def get_all_tasks(
    db: Session,
    offset: int = 0,
    limit: int = 40
):
    try:
        task_list = (
            db.query(Task)
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            tasks.Task.model_validate(task)
            for task in task_list
        ]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks."
        )


def update_task_status(
    task_id: uuid.UUID,
    new_status: str,
    db: Session
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        task.status = new_status

        db.commit()
        db.refresh(task)

        return tasks.Task.model_validate(task)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task status due to a database error."
        )


def update_task_result(
    task_id: uuid.UUID,
    result_reference: str | None,
    error_message: str | None,
    db: Session
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        task.result_reference = result_reference
        task.error_message = error_message

        db.commit()
        db.refresh(task)

        return tasks.Task.model_validate(task)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task result due to a database error."
        )


def delete_task(
    task_id: uuid.UUID,
    db: Session
):
    try:
        task = db.query(Task).filter(
            Task.id == task_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        db.delete(task)
        db.commit()

        return {
            "detail": "Task deleted successfully."
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task due to a database error."
        )
