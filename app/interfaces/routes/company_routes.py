from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.interfaces.schemas.company_schema import (
    CompanyCreateRequest, CompanyUpdateRequest,
    CompanyResponse,
)
from app.application.company.company_use_cases import (
    ListCompaniesUseCase, CreateCompanyUseCase, UpdateCompanyUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/companies", tags=["Companies"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin      = Depends(require_roles(["admin"]))
_all_staff  = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))
_table_ops  = Depends(require_roles(["admin", "mesero", "cajero"]))

def _repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)

@route_message("Empresas obtenidas correctamente")
@router.get("", dependencies=[_all_staff])
def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: CompanyRepository = Depends(_repo),
):
    return ListCompaniesUseCase(repo).execute(page=page, page_size=page_size)

@route_message("Empresa creada correctamente")
@router.post("", response_model=CompanyResponse, status_code=201, dependencies=[_admin])
def create_company(data: CompanyCreateRequest, db:Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateCompanyUseCase(uow.companies).execute(data)
    uow.commit()
    return result