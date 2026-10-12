from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.table_schema import (
    TableCreateRequest, TableUpdateRequest,
    TableStatusRequest, TableResponse,
)
from app.application.table.table_use_cases import (
    ListTablesUseCase, CreateTableUseCase, UpdateTableUseCase,
    UpdateTableStatusUseCase, DeleteTableUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.table_repository import TableRepository

router = APIRouter(prefix="/tables", tags=["Tables"])

_admin      = Depends(require_roles(["admin"]))
_all_staff  = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))
_table_ops  = Depends(require_roles(["admin", "mesero", "cajero"]))


def _repo(db: Session = Depends(get_db)) -> TableRepository:
    return TableRepository(db)


@router.get("", response_model=list[TableResponse], dependencies=[_all_staff])
def list_tables(repo: TableRepository = Depends(_repo)):
    return ListTablesUseCase(repo).execute()


@router.post("", response_model=TableResponse, status_code=201, dependencies=[_admin])
def create_table(data: TableCreateRequest, db: Session = Depends(get_db)):
    result = CreateTableUseCase(TableRepository(db)).execute(data)
    db.commit()
    return result


@router.put("/{table_id}", response_model=TableResponse, dependencies=[_admin])
def update_table(table_id: UUID, data: TableUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateTableUseCase(TableRepository(db)).execute(table_id, data)
    db.commit()
    return result


@router.patch("/{table_id}/status", response_model=TableResponse, dependencies=[_table_ops])
def update_status(table_id: UUID, data: TableStatusRequest, db: Session = Depends(get_db)):
    result = UpdateTableStatusUseCase(TableRepository(db)).execute(table_id, data)
    db.commit()
    return result


@router.delete("/{table_id}", dependencies=[_admin])
def delete_table(table_id: UUID, db: Session = Depends(get_db)):
    result = DeleteTableUseCase(TableRepository(db)).execute(table_id)
    db.commit()
    return result