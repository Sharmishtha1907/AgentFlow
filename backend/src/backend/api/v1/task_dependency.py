
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.crud import task_dependency_crud as dependency_crud
from backend.schemas import task_dependency as dependency_schema


router = APIRouter(
    prefix="/task-dependencies",
    tags=["Task Dependencies"]
)


# CREATE: Create a dependency between two tasks
@router.post(
    "",
    response_model=dependency_schema.TaskDependency,
    status_code=201
)
def create_task_dependency(
    input: dependency_schema.TaskDependencyCreate,
    db: Session = Depends(get_db)
):
    return dependency_crud.create_task_dependency(
        input=input,
        db=db
    )


# READ: Get dependency by ID
@router.get(
    "/{dependency_id}",
    response_model=dependency_schema.TaskDependency,
    status_code=200
)
def get_dependency_by_id(
    dependency_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return dependency_crud.get_dependency_by_id(
        dependency_id=dependency_id,
        db=db
    )


# READ: Get prerequisites of a task
@router.get(
    "/task/{task_id}",
    response_model=list[dependency_schema.TaskDependency],
    status_code=200
)
def get_dependencies_by_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return dependency_crud.get_dependencies_by_task(
        task_id=task_id,
        db=db
    )


# READ: Get tasks that depend on a particular task
@router.get(
    "/task/{task_id}/dependents",
    response_model=list[dependency_schema.TaskDependency],
    status_code=200
)
def get_dependents_by_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return dependency_crud.get_dependents_by_task(
        task_id=task_id,
        db=db
    )


# READ: Get all dependencies belonging to an execution
@router.get(
    "/execution/{execution_id}",
    response_model=list[dependency_schema.TaskDependency],
    status_code=200
)
def get_dependencies_by_execution(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return dependency_crud.get_dependencies_by_execution(
        execution_id=execution_id,
        db=db
    )


# DELETE: Delete a dependency
@router.delete(
    "/{dependency_id}",
    status_code=200
)
def delete_task_dependency(
    dependency_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return dependency_crud.delete_task_dependency(
        dependency_id=dependency_id,
        db=db
    )
