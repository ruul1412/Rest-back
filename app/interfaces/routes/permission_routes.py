from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.interfaces.schemas.permission_schema import (
    AssignPermissionsRequest,
    PermissionResponse,
    UserPermissionResponse,
    RevokePermissionRequest,
)
from app.application.permission.permission_use_cases import (
    ListPermissionsUseCase,
    GetUserPermissionsUseCase,
    AssignPermissionsUseCase,
    RevokePermissionUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_permission
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/permissions", tags=["Permissions"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


# ── GET /permissions ──────────────────────────────────────────────────────────
@route_message("Permisos obtenidos correctamente")
@router.get(
    "",
    dependencies=[Depends(require_permission("permissions.read"))],
)
def list_permissions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return ListPermissionsUseCase(PermissionRepository(db)).execute(page=page, page_size=page_size)


# ── GET /permissions/users/{user_id} ─────────────────────────────────────────
@route_message("Permisos del usuario obtenidos correctamente")
@router.get(
    "/users/{user_id}",
    response_model=list[UserPermissionResponse],
    dependencies=[Depends(require_permission("permissions.read"))],
)
def get_user_permissions(user_id: UUID, db: Session = Depends(get_db)):
    return GetUserPermissionsUseCase(
        perm_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    ).execute(user_id)


# ── POST /permissions/users/{user_id}/assign ──────────────────────────────────
@route_message("Permisos asignados correctamente")
@router.post(
    "/users/{user_id}/assign",
    dependencies=[Depends(require_permission("permissions.assign"))],
)
def assign_permissions(
    user_id: UUID,
    data: AssignPermissionsRequest,
    db: Session = Depends(get_db),
):
    uow = UnitOfWork(db)
    result = AssignPermissionsUseCase(
        perm_repo=uow.permissions,
        user_repo=uow.users,
    ).execute(user_id, data)
    uow.commit()
    return result


# ── DELETE /permissions/users/{user_id}/revoke ────────────────────────────────
@route_message("Permisos revocados correctamente")
@router.delete(
    "/users/{user_id}/revoke",
    dependencies=[Depends(require_permission("permissions.assign"))],
)
def revoke_permission(
    user_id: UUID,
    data: RevokePermissionRequest,
    db: Session = Depends(get_db),
):
    uow = UnitOfWork(db)
    result = RevokePermissionUseCase(
        perm_repo=uow.permissions,
        user_repo=uow.users,
    ).execute(user_id, data)
    uow.commit()
    return result