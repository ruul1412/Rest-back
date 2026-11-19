from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.company_schema import (
    CompanyCreateRequest, CompanyUpdateRequest,
    CompanyResponse, CompanyStatusUpdateRequest
)
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.core.pagination import build_paginated_response, normalize_pagination
from app.interfaces.schemas.company_schema import ( 
    CompanyResponse,
    CompanyCreateRequest,
    CompanyUpdateRequest,
)


def _resp(e) -> CompanyResponse:
    return CompanyResponse(id=e.id, name=e.name, description=e.description, phone=e.phone, is_active=e.is_active,ruc=e.ruc)

class ListCompaniesUseCase:
    def __init__(self, repo: CompanyRepository): self.__repo=repo

    def execute(self, page: int = 1, page_size: int | None = None) -> dict:
        page, page_size, skip = normalize_pagination(page, page_size)
        items = [_resp(e) for e in self.__repo.get_all(skip=skip, limit=page_size)]
        total = self.__repo.count()
        return build_paginated_response(items, total, page, page_size)
    
class CreateCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self, request: CompanyCreateRequest) -> CompanyResponse:
        company = self._repo.create(name=request.name, description=request.description, phone=request.phone,ruc=request.ruc)
        return _resp(company)

class UpdateCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self, company_id: UUID, request: CompanyUpdateRequest) -> CompanyResponse:
        if request.name and self._repo.name_exists(request.name, exclude_id=company_id):
            raise HTTPException(status_code=400, detail=f"Ya existe la empresa con el nombre {request.name}")
        company = self._repo.update(company_id, name=request.name, description=request.description, phone=request.phone, is_active=request.is_active,ruc=request.ruc)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return _resp(company)

class UpdateCompanyStatusUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self, company_id: UUID, request: CompanyStatusUpdateRequest) -> CompanyResponse:
        company = self._repo.updateStatus(company_id, request.is_active)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return _resp(company)    

class DeleteCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self._repo = repo

    def execute(self, company_id: UUID) -> None:
        if not self._repo.delete(company_id):
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return {"detail": "Empresa eliminada"}