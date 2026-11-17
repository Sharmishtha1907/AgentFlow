
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.database.models import (
    Task,
    TaskDependency,
    Execution
)
from backend.schemas import task_dependency as dependency_schema


def create_task_dependency(
    input: dependency_schema.TaskDependencyCreate,
    db: Session
):
    try:
        task = db.query(Task).filter(
            Task.id == input.task_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dependent task not found."
            )

        # Get the prerequisite task
        prerequisite = db.query(Task).filter(
            Task.id == input.depends_on_task_id
        ).first()

        if not prerequisite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prerequisite task not found."
            )

        # Both tasks must belong to the same execution.
        # Lock the execution row to serialize dependency changes within this execution.
        if task.execution_id != prerequisite.execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both tasks must belong to the same execution."
            )

        execution = (
            db.query(Execution)
            .filter(Execution.id == task.execution_id)
            .with_for_update()
            .first()
        )

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found."
            )

        # Prevent duplicate dependencies
        existing_dependency = db.query(TaskDependency).filter(
            TaskDependency.task_id == input.task_id,
            TaskDependency.depends_on_task_id == input.depends_on_task_id
        ).first()

        if existing_dependency:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This task dependency already exists."
            )

        # Load existing dependency relationships for this execution.
        # Each edge means: task_id depends on depends_on_task_id.
        existing_edges = (
            db.query(TaskDependency)
            .join(
                Task,
                TaskDependency.task_id == Task.id
            )
            .filter(Task.execution_id == task.execution_id)
            .all()
        )

        # Build adjacency list:
        # task_id -> list of prerequisite task IDs
        graph = {}

        for edge in existing_edges:
            graph.setdefault(edge.task_id, []).append(
                edge.depends_on_task_id
            )

        # Check whether adding this dependency creates a cycle.
        # Start from the prerequisite and follow its prerequisites.
        # If we reach the dependent task, a cycle would be created.
        visited = set()
        stack = [input.depends_on_task_id]

        while stack:
            current_task_id = stack.pop()

            if current_task_id == input.task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This dependency would create a circular dependency."
                )

            if current_task_id in visited:
                continue

            visited.add(current_task_id)

            stack.extend(graph.get(current_task_id, []))

        # Create the dependency
        dependency = TaskDependency(
            task_id=input.task_id,
            depends_on_task_id=input.depends_on_task_id
        )

        db.add(dependency)
        db.commit()
        db.refresh(dependency)

        return dependency_schema.TaskDependency.model_validate(
            dependency
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task dependency conflicts with an existing database constraint."
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task dependency due to a database error."
        )


# READ: Get a dependency by ID
def get_dependency_by_id(
    dependency_id: uuid.UUID,
    db: Session
):
    try:
        dependency = db.query(TaskDependency).filter(
            TaskDependency.id == dependency_id
        ).first()

        if not dependency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task dependency not found."
            )

        return dependency_schema.TaskDependency.model_validate(
            dependency
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task dependency."
        )


# READ: Get all prerequisites of a task
def get_dependencies_by_task(
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

        dependencies = db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id
        ).all()

        return [
            dependency_schema.TaskDependency.model_validate(dep)
            for dep in dependencies
        ]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task prerequisites."
        )


# READ: Get all tasks that depend on a particular task
def get_dependents_by_task(
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

        dependents = db.query(TaskDependency).filter(
            TaskDependency.depends_on_task_id == task_id
        ).all()

        return [
            dependency_schema.TaskDependency.model_validate(dep)
            for dep in dependents
        ]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dependent tasks."
        )


# READ: Get all dependencies belonging to an execution
def get_dependencies_by_execution(
    execution_id: uuid.UUID,
    db: Session
):
    try:
        execution = db.query(Execution).filter(
            Execution.id == execution_id
        ).first()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found."
            )

        dependencies = (
            db.query(TaskDependency)
            .join(
                Task,
                TaskDependency.task_id == Task.id
            )
            .filter(Task.execution_id == execution_id)
            .all()
        )

        return [
            dependency_schema.TaskDependency.model_validate(dep)
            for dep in dependencies
        ]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch execution dependencies."
        )


# DELETE: Delete a task dependency
def delete_task_dependency(
    dependency_id: uuid.UUID,
    db: Session
):
    try:
        dependency = db.query(TaskDependency).filter(
            TaskDependency.id == dependency_id
        ).first()

        if not dependency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task dependency not found."
            )

        db.delete(dependency)
        db.commit()

        return {
            "detail": "Task dependency deleted successfully."
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task dependency."
        )
