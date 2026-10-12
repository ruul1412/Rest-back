from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.permission_schema import (
    AssignPermissionsRequest,
    PermissionResponse,
    UserPermissionResponse,
    RevokePermissionRequest,
)
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.infrastructure.repositories.user_repository import UserRepository


def _to_response(entity) -> PermissionResponse:
    return PermissionResponse(
        id=entity.id,
        code=entity.code,
        description=entity.description,
    )


def _to_user_perm_response(entity) -> UserPermissionResponse:
    return UserPermissionResponse(
        id=entity.id,
        code=entity.code,
        description=entity.description,
        granted_by=entity.granted_by,
        expires_at=entity.expires_at,
        reason=entity.reason,
    )


class ListPermissionsUseCase:
    def __init__(self, repo: PermissionRepository): self._repo = repo

    def execute(self) -> list[PermissionResponse]:
        return [_to_response(e) for e in self._repo.get_all()]


class GetUserPermissionsUseCase:
    def __init__(self, perm_repo: PermissionRepository, user_repo: UserRepository):
        self._perm_repo = perm_repo
        self._user_repo = user_repo

    def execute(self, user_id: UUID) -> list[UserPermissionResponse]:
        if not self._user_repo.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return [_to_user_perm_response(e) for e in self._perm_repo.get_by_user(user_id)]


class AssignPermissionsUseCase:
    """
    Reemplaza los permisos directos del usuario.
    Registra quién los otorgó, cuándo vencen y por qué razón.
    """
    def __init__(self, perm_repo: PermissionRepository, user_repo: UserRepository):
        self._perm_repo = perm_repo
        self._user_repo = user_repo

    def execute(self, user_id: UUID, data: AssignPermissionsRequest) -> dict:
        if not self._user_repo.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        all_exist, missing = self._perm_repo.codes_exist(data.permission_codes)
        if not all_exist:
            raise HTTPException(
                status_code=404,
                detail=f"Permisos no encontrados: {', '.join(missing)}",
            )

        self._perm_repo.assign_to_user(
            user_id=user_id,
            codes=data.permission_codes,
            granted_by=data.granted_by,
            expires_at=data.expires_at,
            reason=data.reason,
        )

        count = len(data.permission_codes)
        if count == 0:
            return {"detail": "Todos los permisos directos han sido revocados"}
        return {"detail": f"{count} permiso(s) asignado(s) correctamente"}


class RevokePermissionUseCase:
    def __init__(self, perm_repo: PermissionRepository, user_repo: UserRepository):
        self._perm_repo = perm_repo
        self._user_repo = user_repo

    def execute(self, user_id: UUID, data: RevokePermissionRequest) -> dict:
        if not self._user_repo.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        ok = self._perm_repo.revoke_from_user(user_id, data.permission_code)
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"El permiso '{data.permission_code}' no existe o no estaba asignado",
            )
        return {"detail": f"Permiso '{data.permission_code}' revocado correctamente"}