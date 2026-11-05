from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.company_schemas import (
    CompanyCreateRequest, CompanyResponse
)
from app.application.company.company_use_cases import (
    ListCompanyUseCase,CreateCompanyUseCase
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.company_repository import CompanyRepository

router = APIRouter(prefix="/company", tags=["Companys"])

_admin      = Depends(require_roles(["admin"]))
_all_staff  = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))

def _repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


@router.get("", response_model=list[CompanyResponse], dependencies=[_all_staff])
def list_company(repo: CompanyRepository = Depends(_repo)):
    return ListCompanyUseCase(repo).execute()


@router.post("", response_model=CompanyResponse, status_code=201, dependencies=[_admin])
def create_company(data: CompanyCreateRequest, db: Session = Depends(get_db)):
    result = CreateCompanyUseCase(CompanyRepository(db)).execute(data)
    db.commit()
    return result