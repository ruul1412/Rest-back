from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.company_schema import (
    CompanyCreateRequest, CompanyUpdateRequest,
    CompanyResponse,
)
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.core.pagination import build_paginated_response, normalize_pagination
from app.interfaces.schemas.table_schema import TableResponse


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
    def __init__(self, repo: CompanyRepository): self.__repo=repo

    def execute(self, data: CompanyCreateRequest) -> CompanyResponse:
        #implementar busqueda por nombre para evitar duplicados
       # if self.__repo.get_by_name(data.name):
       #     raise HTTPException(status_code=400, detail="El nombre de la empresa ya existe")
        return _resp(self.__repo.create(data.name, data.description, data.phone, data.ruc))
    
class UpdateCompanyUseCase:
    def __init__(self, repo: CompanyRepository): self.__repo=repo

    def execute(self, company_id: UUID, data: CompanyUpdateRequest) ->CompanyResponse:
        #colocar el mismo if de la linea 30
       # if self.__repo.get_by_name(data.name):
       #     raise HTTPException(status_code=400, detail="El nombre de la empresa ya existe")
        entity = self.__repo.update(company_id, data.name, data.description, data.phone, data.is_active, data.ruc)
        if not entity:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return _resp(entity)