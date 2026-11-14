from uuid import UUID

from fastapi import HTTPException

from app.infrastructure.repositories.branch_repository import BranchRepository
from app.interfaces.schemas.branch_schema import (
    BranchCreateRequest, BranchUpdateRequest,
    BranchResponse,
)
from app.core.pagination import build_paginated_response, normalize_pagination
from app.interfaces.schemas.branch_schema import BranchResponse
from app.interfaces.schemas.table_schema import TableResponse


def _resp(e) -> BranchResponse:
    return BranchResponse(id=e.id, name=e.name, description=e.description, phone=e.phone, address=e.address)

class ListBranchesUseCase:
    def __init__(self, repo: BranchRepository): self.__repo=repo

    def execute(self, page: int = 1, page_size: int | None = None) -> dict:
        page, page_size, skip = normalize_pagination(page, page_size)
        items = [_resp(e) for e in self.__repo.get_all(skip=skip, limit=page_size)]
        total = self.__repo.count()
        return build_paginated_response(items, total, page, page_size)