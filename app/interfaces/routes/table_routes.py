from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/tables", tags=["Tables"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin      = Depends(require_roles(["admin"]))
_all_staff  = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))
_table_ops  = Depends(require_roles(["admin", "mesero", "cajero"]))


def _repo(db: Session = Depends(get_db)) -> TableRepository:
    return TableRepository(db)


@route_message("Mesas obtenidas correctamente")
@router.get("", dependencies=[_all_staff])
def list_tables(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: TableRepository = Depends(_repo),
):
    return ListTablesUseCase(repo).execute(page=page, page_size=page_size)


@route_message("Mesa creada correctamente")
@router.post("", response_model=TableResponse, status_code=201, dependencies=[_admin])
def create_table(data: TableCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateTableUseCase(uow.tables).execute(data)
    uow.commit()
    return result


@route_message("Mesa actualizada correctamente")
@router.put("/{table_id}", response_model=TableResponse, dependencies=[_admin])
def update_table(table_id: UUID, data: TableUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateTableUseCase(uow.tables).execute(table_id, data)
    uow.commit()
    return result


@route_message("Estado de la mesa actualizado correctamente")
@router.patch("/{table_id}/status", response_model=TableResponse, dependencies=[_table_ops])
def update_status(table_id: UUID, data: TableStatusRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateTableStatusUseCase(uow.tables).execute(table_id, data)
    uow.commit()
    return result


@route_message("Mesa eliminada correctamente")
@router.delete("/{table_id}", dependencies=[_admin])
def delete_table(table_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteTableUseCase(uow.tables).execute(table_id)
    uow.commit()
    return result