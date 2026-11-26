
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.domain.user.user_entity import UserEntity


security = HTTPBearer()


def get_current_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:

    payload = decode_access_token(credentials.credentials)

    user_id = payload.get("sub")
    scope = payload.get("scope")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    try:
        user_id = UUID(str(user_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Identificador de usuario inválido"
        )

    repo = UserRepository(db)

    # 1. Validar cuenta global
    user = repo.get_by_id(user_id)

    if not user or user.is_deleted:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Usuario inactivo"
        )

    # 2. Super administrador: acceso global
    if scope == "platform":

        if (
            payload.get("role_code") != "super_admin"
            or user.role_code != "super_admin"
        ):
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos de administrador de plataforma"
            )

        return {
            "user": user,
            "payload": payload
        }

    # 3. Usuario con contexto de sucursal
    if scope == "branch":

        branch_id = payload.get("branch_id")
        company_id = payload.get("company_id")

        if not branch_id or not company_id:
            raise HTTPException(
                status_code=401,
                detail="Token de sucursal inválido"
            )

        try:
            branch_id = UUID(str(branch_id))
            company_id = UUID(str(company_id))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=401,
                detail="Identificadores del token inválidos"
            )

        # Comprobar membresía, sucursal y empresa
        membership = repo.get_active_membership(
            user.id,
            branch_id
        )

        if not membership:
            raise HTTPException(
                status_code=403,
                detail="Tu acceso a esta sucursal está deshabilitado"
            )

        # Comprobar que el contexto del token siga vigente
        if (
            membership.company_id != company_id
            or membership.role_code != payload.get("role_code")
        ):
            raise HTTPException(
                status_code=403,
                detail="Tu sesión ha cambiado. Inicia sesión nuevamente"
            )

        return {
            "user": user,
            "payload": payload
        }

    raise HTTPException(
        status_code=403,
        detail="Tipo de acceso no permitido"
    )


# ---------------------------------------------------------
# USUARIO AUTENTICADO
# ---------------------------------------------------------

def get_current_user(
    context: dict = Depends(get_current_auth_context),
) -> UserEntity:

    return context["user"]


# ---------------------------------------------------------
# SUPER ADMIN
# ---------------------------------------------------------

def require_platform_admin():

    def _checker(
        context: dict = Depends(get_current_auth_context)
    ):

        payload = context["payload"]

        if (
            payload.get("scope") != "platform"
            or payload.get("role_code") != "super_admin"
        ):
            raise HTTPException(
                status_code=403,
                detail="Esta operación requiere permisos de Super Admin"
            )

        return payload

    return _checker


# ---------------------------------------------------------
# ROLES OPERATIVOS
# ---------------------------------------------------------

def require_roles(roles: list[str]):

    def _checker(
        context: dict = Depends(get_current_auth_context)
    ) -> UserEntity:

        payload = context["payload"]

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

        return context["user"]

    return _checker


# ---------------------------------------------------------
# PERMISOS
# ---------------------------------------------------------

def require_permission(permission_code: str):

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


# ---------------------------------------------------------
# GESTIÓN DE USUARIOS
# ---------------------------------------------------------

def require_user_management():

    def _checker(
        context: dict = Depends(get_current_auth_context)
    ):

        payload = context["payload"]

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
