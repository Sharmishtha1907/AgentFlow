
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.crud import tasks_crud
from backend.schemas import tasks as task_schema


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)



@router.post(
    "",
    response_model=task_schema.Task,
    status_code=status.HTTP_201_CREATED
)
def create_task(
    input: task_schema.TaskCreate,
    db: Session = Depends(get_db)
):
    return tasks_crud.create_task(
        input=input,
        db=db
    )


@router.get(
    "",
    response_model=list[task_schema.Task],
    status_code=status.HTTP_200_OK
)
def get_all_tasks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return tasks_crud.get_all_tasks(
        db=db,
        offset=offset,
        limit=limit
    )


@router.get(
    "/execution/{execution_id}",
    response_model=list[task_schema.Task],
    status_code=status.HTTP_200_OK
)
def get_tasks_by_execution(
    execution_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return tasks_crud.get_tasks_by_execution(
        execution_id=execution_id,
        db=db,
        offset=offset,
        limit=limit
    )


@router.get(
    "/{task_id}",
    response_model=task_schema.Task,
    status_code=status.HTTP_200_OK
)
def get_task_by_id(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return tasks_crud.get_task_by_id(
        task_id=task_id,
        db=db
    )


@router.patch(
    "/{task_id}/status",
    response_model=task_schema.Task,
    status_code=status.HTTP_200_OK
)
def update_task_status(
    task_id: uuid.UUID,
    input: task_schema.TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    return tasks_crud.update_task_status(
        task_id=task_id,
        new_status=input.new_status,
        db=db
    )


@router.patch(
    "/{task_id}/result",
    response_model=task_schema.Task,
    status_code=status.HTTP_200_OK
)
def update_task_result(
    task_id: uuid.UUID,
    input: task_schema.TaskResultUpdate,
    db: Session = Depends(get_db)
):
    return tasks_crud.update_task_result(
        task_id=task_id,
        result_reference=input.result_reference,
        error_message=input.error_message,
        db=db
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK
)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return tasks_crud.delete_task(
        task_id=task_id,
        db=db
    )
