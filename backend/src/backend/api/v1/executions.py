
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.crud import execution_crud
from backend.schemas import execution as execution_schema


router = APIRouter(
    prefix="/executions",
    tags=["Executions"]
)


@router.post(
    "",
    response_model=execution_schema.Execution,
    status_code=status.HTTP_201_CREATED
)
def create_execution(
    input: execution_schema.ExecutionCreate,
    db: Session = Depends(get_db)
):
    return execution_crud.create_execution(
        input=input,
        db=db
    )


@router.get(
    "/{execution_id}",
    response_model=execution_schema.Execution,
    status_code=status.HTTP_200_OK
)
def get_execution_by_id(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return execution_crud.get_execution_by_id(
        execution_id=execution_id,
        db=db
    )


@router.get(
    "/user/{user_id}",
    response_model=list[execution_schema.Execution],
    status_code=status.HTTP_200_OK
)
def get_executions_by_user(
    user_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return execution_crud.get_executions_by_user(
        user_id=user_id,
        db=db,
        offset=offset,
        limit=limit
    )


@router.get(
    "",
    response_model=list[execution_schema.Execution],
    status_code=status.HTTP_200_OK
)
def get_all_executions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=40, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return execution_crud.get_all_executions(
        db=db,
        offset=offset,
        limit=limit
    )



@router.patch(
    "/{execution_id}/status",
    response_model=execution_schema.Execution,
    status_code=status.HTTP_200_OK
)
def update_execution_status(
    execution_id: uuid.UUID,
    input: execution_schema.ExecutionStatusUpdate,
    db: Session = Depends(get_db)
):
    return execution_crud.update_execution_status(
        execution_id=execution_id,
        new_status=input.new_status,
        db=db
    )


@router.patch(
    "/{execution_id}/result",
    response_model=execution_schema.Execution,
    status_code=status.HTTP_200_OK
)
def update_execution_final_result(
    execution_id: uuid.UUID,
    input: execution_schema.ExecutionFinalResultUpdate,
    db: Session = Depends(get_db)
):
    return execution_crud.update_execution_final_result(
        execution_id=execution_id,
        final_result=input.final_result,
        db=db
    )


# DELETE: Delete execution
@router.delete(
    "/{execution_id}",
    status_code=status.HTTP_200_OK
)
def delete_execution(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return execution_crud.delete_execution(
        execution_id=execution_id,
        db=db
    )
