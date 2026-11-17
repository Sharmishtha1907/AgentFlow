
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.crud import task_result_crud
from backend.schemas import task_result as task_result_schema


router = APIRouter(
    prefix="/task-results",
    tags=["Task Results"]
)


# 1. Get a task result by its ID
@router.get("/{result_id}", response_model=task_result_schema.TaskResult)
def get_task_result(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    return task_result_crud.get_task_result_by_id(
        result_id=result_id,
        db=db
    )


# 2. Get all results belonging to a task
@router.get(
    "/task/{task_id}",
    response_model=list[task_result_schema.TaskResult]
)
def get_task_results_by_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    return task_result_crud.get_task_results_by_task(
        task_id=task_id,
        db=db
    )


# 3. Get a result for a specific task attempt
@router.get(
    "/task/{task_id}/attempt/{attempt_number}",
    response_model=task_result_schema.TaskResult
)
def get_task_result_by_attempt(
    task_id: UUID,
    attempt_number: int,
    db: Session = Depends(get_db)
):
    return task_result_crud.get_task_result_by_attempt(
        task_id=task_id,
        attempt_number=attempt_number,
        db=db
    )


# 4. Get all task results (paginated)
@router.get(
    "",
    response_model=list[task_result_schema.TaskResult]
)
def get_all_task_results(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return task_result_crud.get_all_task_results(
        offset=offset,
        limit=limit,
        db=db
    )
