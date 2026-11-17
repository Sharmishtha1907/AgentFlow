
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.crud import task_attempt_crud as task_attempt

router = APIRouter(
    prefix="/task-attempts",
    tags=["Task Attempts"]
)


@router.get("/{attempt_id}")
def get_task_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db)
):
    return task_attempt.get_attempt_by_id(
        attempt_id=attempt_id,
        db=db
    )


@router.get("/task/{task_id}")
def get_task_attempts_by_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    return task_attempt.get_attempts_by_task(
        task_id=task_id,
        db=db
    )


@router.get("")
def get_all_task_attempts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return task_attempt.get_all_attempts(
        offset=offset,
        limit=limit,
        db=db
    )
