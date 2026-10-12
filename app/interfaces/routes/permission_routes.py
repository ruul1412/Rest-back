from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# ── GET /permissions ──────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permission("permissions.read"))],
)
def list_permissions(db: Session = Depends(get_db)):
    return ListPermissionsUseCase(PermissionRepository(db)).execute()


# ── GET /permissions/users/{user_id} ─────────────────────────────────────────
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
@router.post(
    "/users/{user_id}/assign",
    dependencies=[Depends(require_permission("permissions.assign"))],
)
def assign_permissions(
    user_id: UUID,
    data: AssignPermissionsRequest,
    db: Session = Depends(get_db),
):
    result = AssignPermissionsUseCase(
        perm_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    ).execute(user_id, data)
    db.commit()
    return result


# ── DELETE /permissions/users/{user_id}/revoke ────────────────────────────────
@router.delete(
    "/users/{user_id}/revoke",
    dependencies=[Depends(require_permission("permissions.assign"))],
)
def revoke_permission(
    user_id: UUID,
    data: RevokePermissionRequest,
    db: Session = Depends(get_db),
):
    result = RevokePermissionUseCase(
        perm_repo=PermissionRepository(db),
        user_repo=UserRepository(db),
    ).execute(user_id, data)
    db.commit()
    return result