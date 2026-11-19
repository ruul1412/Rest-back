from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.interfaces.schemas.branch_schema import (
    BranchCreateRequest, BranchUpdateRequest,
    BranchResponse,
)
from app.application.branch.branch_use_cases import (
    ListBranchesUseCase
)
from app.interfaces.dependencies.auth_dependencies import require_platform_admin
from app.infrastructure.repositories.branch_repository import BranchRepository
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/branches", tags=["Branches"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_platform_admin = Depends(require_platform_admin())


def _repo(db: Session = Depends(get_db)) -> BranchRepository:
    return BranchRepository(db)

@route_message("Sucursales obtenidas correctamente")
@router.get("", dependencies=[_platform_admin])
def list_branches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: BranchRepository = Depends(_repo),
):
    return ListBranchesUseCase(repo).execute(page=page, page_size=page_size)

# @route_message("Sucursal creada correctamente")
# @router.post("", response_model=BranchResponse, status_code=201, dependencies=[_admin])
# def create_branch(data: BranchCreateRequest, db:Session = Depends(get_db)):
#     uow = UnitOfWork(db)
#     result = CreateBranchUseCase(uow.branches).execute(data)
#     uow.commit()
#     return result



