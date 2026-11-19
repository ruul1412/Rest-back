from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.company.company_use_cases import UpdateCompanyStatusUseCase
from app.core.config import settings
from app.core.database import get_db
from app.interfaces.schemas.branch_schema import (
    BranchCreateRequest, BranchUpdateRequest,
    BranchResponse, BranchStatusUpdateRequest
)
from app.application.branch.branch_use_cases import (
    ListBranchesUseCase, ListBranchesByCompanyUseCase, CreateBranchUseCase, UpdateBranchUseCase, DeleteBranchUseCase, UpdateBranchStatusUseCase
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.branch_repository import BranchRepository
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/branches", tags=["Branches"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin      = Depends(require_roles(["admin"]))
_all_staff  = Depends(require_roles(["admin", "me"
"sero", "cajero", "cocina", "bartender"]))
_table_ops  = Depends(require_roles(["admin", "mesero", "cajero"]))

def _repo(db: Session = Depends(get_db)) -> BranchRepository:
    return BranchRepository(db)

@route_message("Sucursales obtenidas correctamente")
@router.get("", dependencies=[_all_staff])
#agragar un filtro por company_id, para obtener solo las sucursales de una empresa especifica
def list_branches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: BranchRepository = Depends(_repo),
):
    return ListBranchesUseCase(repo).execute(page=page, page_size=page_size)

@route_message("Sucursales obtenidas compania")
@router.get("/byCompany/{company_id}", dependencies=[_all_staff])
def list_branches_by_company(
    company_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: BranchRepository = Depends(_repo),
):
    return ListBranchesByCompanyUseCase(repo).execute(company_id=company_id, page=page, page_size=page_size)


@route_message("Sucursal creada correctamente")
@router.post("", response_model=BranchResponse, status_code=201, dependencies=[_admin])
def create_branch(data: BranchCreateRequest, db:Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateBranchUseCase(uow.branches).execute(data)
    uow.commit()
    return result

@route_message("Sucursal actualizada correctamente")
@router.put("/{branch_id}", response_model=BranchResponse, dependencies=[_admin])
def update_branch(branch_id: UUID, data: BranchUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateBranchUseCase(uow.branches).execute(branch_id, data)
    uow.commit()
    return result

@route_message("Estado de la Sucursal actualizada correctamente")
@router.patch("/{branch_id}/status", response_model=BranchResponse, dependencies=[_admin])
def update_status_branch(branch_id: UUID, data: BranchStatusUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateBranchStatusUseCase(uow.branches).execute(branch_id, data)
    uow.commit()
    return result

@route_message("Sucursal eliminada correctamente")
@router.delete("/{branch_id}", dependencies=[_admin])
def delete_branch(branch_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteBranchUseCase(uow.branches).execute(branch_id)
    uow.commit()
    return result