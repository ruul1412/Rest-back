from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.domain.user.user_entity import UserEntity

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserEntity:
    payload = decode_access_token(credentials.credentials)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = UserRepository(db).get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    return user


def require_roles(roles: list[str]):
    def _checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        payload = decode_access_token(credentials.credentials)

        if payload.get("scope") != "branch":
            raise HTTPException(
                status_code=403,
                detail="Esta operación requiere un contexto de sucursal"
            )

        if payload.get("role_code") not in roles:
            raise HTTPException(
                status_code=403,
                detail="No autorizado"
            )

        return payload

    return _checker

def require_permission(permission_code: str):
    """
    Verifica que el usuario tenga un permiso específico activo,
    ya sea heredado por su rol o asignado directamente.

    Uso:
        # Solo como guardia:
        @router.get("/ruta", dependencies=[Depends(require_permission("orders.read"))])

        # Con acceso al usuario autenticado:
        @router.get("/ruta")
        def endpoint(user = Depends(require_permission("orders.read"))):
            ...
    """
    def _checker(
        user: UserEntity = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> UserEntity:
        effective = PermissionRepository(db).get_effective_codes(user.id)
        if permission_code not in effective:
            raise HTTPException(
                status_code=403,
                detail=f"Se requiere el permiso '{permission_code}'",
            )
        return user
    return _checker

def require_user_management():
    def _checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        payload = decode_access_token(credentials.credentials)

        scope = payload.get("scope")
        role_code = payload.get("role_code")

        if scope == "platform" and role_code == "super_admin":
            return payload

        if scope == "branch" and role_code == "admin":
            return payload

        raise HTTPException(
            status_code=403,
            detail="No autorizado para gestionar usuarios"
        )

    return _checker