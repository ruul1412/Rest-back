from uuid import UUID

from fastapi import HTTPException
from app.interfaces.schemas.company_schemas import (
    CompanyCreateRequest, CompanyResponse
)
from app.infrastructure.repositories.company_repository import CompanyRepository

def _resp(e) -> CompanyResponse:
    return CompanyResponse(id=e.id, description=e.description, phone=e.phone, is_active=e.is_active, name=e.name, ruc=e.ruc)


class ListCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self) -> list[CompanyResponse]:
        return [_resp(e) for e in self._repo.get_all()]


class CreateCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self, data: CompanyCreateRequest) -> CompanyResponse:
        if self._repo.ruc_exists(data.ruc):
            raise HTTPException(status_code=400, detail="Ya existe el ruc {data.ruc}")
        return _resp(self._repo.create(data.description, data.phone, data.is_active, data.name, data.ruc))