from backend.database.session import get_db
from backend.schemas import execution
from requests import Session
from backend.database.models import Execution
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

def create_execution(
    input: execution.ExecutionCreate,
    db: Session
):
    try:
        exec = Execution(
            user_id=input.user_id,
            original_request=input.original_request,
            status="PENDING"
        )
        db.add(exec)
        db.commit()
        db.refresh(exec)
        
        return execution.Execution.model_validate(exec)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create execution due to a database error."
        )

def get_execution_by_id(
    execution_id: uuid.UUID,
    db: Session
):
    exec = db.query(Execution).filter(
        Execution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution.Execution.model_validate(exec)

def get_executions_by_user(
    user_id: uuid.UUID,
    db: Session,
    offset: int=0,
    limit: int=20,
):
    try:
        executions = (
            db.query(Execution)
            .filter(Execution.user_id == user_id)
            .order_by(Execution.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [execution.Execution.model_validate(ex) for ex in executions]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch executions for this user."
        )

def get_all_executions(
    db: Session,
    offset: int=0,
    limit: int=40,
):
    try:
        executions = (
            db.query(Execution)
            .order_by(Execution.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [execution.Execution.model_validate(ex) for ex in executions]

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch executions."
        )

def update_execution_status(
    execution_id: uuid.UUID,
    new_status: str,
    db: Session
):
    try:
        exec = db.query(Execution).filter(
            Execution.id == execution_id
        ).first()

        if not exec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        exec.status = new_status
        db.commit()
        db.refresh(exec)

        return execution.Execution.model_validate(exec)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update execution status due to a database error."
        )

def update_execution_final_result(
    execution_id: uuid.UUID,
    final_result: dict,
    db: Session
):
    try:
        exec = db.query(Execution).filter(
            Execution.id == execution_id
        ).first()

        if not exec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        exec.final_result = final_result
        db.commit()
        db.refresh(exec)

        return execution.Execution.model_validate(exec)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update execution final result due to a database error."
        )

def delete_execution(
    execution_id: uuid.UUID,
    db: Session
):
    try:
        exec = db.query(Execution).filter(
            Execution.id == execution_id
        ).first()

        if not exec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )

        db.delete(exec)
        db.commit()

        return {"detail": "Execution deleted successfully."}

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete execution due to a database error."
        )

