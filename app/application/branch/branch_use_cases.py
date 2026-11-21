from uuid import UUID

from fastapi import HTTPException

from app.infrastructure.repositories.branch_repository import BranchRepository
from app.interfaces.schemas.branch_schema import (
    BranchCreateRequest, BranchStatusUpdateRequest, BranchUpdateRequest,
    BranchResponse,
)

from app.infrastructure.repositories.branch_repository import BranchRepository
from app.core.pagination import build_paginated_response, normalize_pagination
from app.interfaces.schemas.branch_schema import( 
    BranchResponse,
    BranchCreateRequest,
    BranchUpdateRequest,
)

def _resp(e) -> BranchResponse:
    return BranchResponse(id=e.id, 
                          name=e.name, 
                          description=e.description, 
                          phone=e.phone, 
                          address=e.address,
                          is_active= e.is_active,
                          company_name = e.company_name)

class ListBranchesUseCase:
    def __init__(self, repo: BranchRepository): self.__repo=repo

    def execute(self, page: int = 1, page_size: int | None = None) -> dict:
        page, page_size, skip = normalize_pagination(page, page_size)
        items = [_resp(e) for e in self.__repo.get_all(skip=skip, limit=page_size)]
        total = self.__repo.count()
        return build_paginated_response(items, total, page, page_size)

#--------------------------------- listar Branch por compania ---------------------------------
class ListBranchesByCompanyUseCase:
    def __init__(self, repo: BranchRepository): self.__repo=repo

    def execute(self, company_id: UUID, page: int = 1, page_size: int | None = None) -> dict:
        page, page_size, skip = normalize_pagination(page, page_size)
        items = [_resp(e) for e in self.__repo.get_by_company(company_id=company_id, skip=skip, limit=page_size)]
        total = self.__repo.count_by_company(company_id=company_id)
        return build_paginated_response(items, total, page, page_size)

class CreateBranchUseCase:
    def __init__(self, repo: BranchRepository): self._repo = repo

    def execute(self, request: BranchCreateRequest) -> BranchResponse:
        branch = self._repo.create(company_id=request.company_id, name=request.name, description=request.description, phone=request.phone, address=request.address)
        return _resp(branch)

class UpdateBranchUseCase:
    def __init__(self, repo: BranchRepository): self._repo = repo

    def execute(self, branch_id: UUID, request: BranchUpdateRequest) -> BranchResponse:
        branch = self._repo.update(branch_id, name=request.name, description=request.description, phone=request.phone, address=request.address)
        if not branch:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        return _resp(branch)

class UpdateBranchStatusUseCase:
    def __init__(self, repo: BranchRepository): self._repo = repo

    def execute(self, branch_id: UUID, request: BranchStatusUpdateRequest) -> BranchResponse:
        branch = self._repo.updateStatus(branch_id, request.is_active)
        if not branch:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        return _resp(branch)      

class DeleteBranchUseCase:
    def __init__(self, repo: BranchRepository): self._repo = repo

    def execute(self, branch_id: UUID) -> None:
        if self._repo.is_occupied(branch_id):
            raise HTTPException(status_code=400, detail="No se puede eliminar una sucursal ocupada")
        if not self._repo.delete(branch_id):
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        return {"detail": "Sucursal eliminada"}