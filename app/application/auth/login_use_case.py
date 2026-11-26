
from fastapi import HTTPException

from app.interfaces.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    BranchOptionResponse
)

from app.infrastructure.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token


_INVALID = HTTPException(
    status_code=401,
    detail="Credenciales inválidas"
)

_INACTIVE = HTTPException(
    status_code=403,
    detail="Usuario inactivo"
)


class LoginUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, data: LoginRequest) -> LoginResponse:

        user = self._repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.password):
            raise _INVALID

        if user.is_deleted:
            raise HTTPException(
                status_code=403,
                detail="La cuenta está eliminada"
            )
        
        if not user.is_active:
            raise _INACTIVE

        # 1. Super administrador: acceso global
        if user.role_code == "super_admin":

            token = create_access_token({
                "sub": str(user.id),
                "role_code": "super_admin",
                "scope": "platform" #  ver que hace el scope
                
            })

            return LoginResponse(access_token=token)

        # 2. Consultar sucursales activas del usuario
        memberships = self._repo.get_active_memberships(user.id)

        if not memberships:
            raise HTTPException(
                status_code=403,
                detail="No tienes ninguna sucursal disponible para ingresar. "
            "Verifica que tu asignación, sucursal y empresa estén activas "
            "o contacta al administrador."
            )

        # Convertir membresías a respuesta
        options = [
            BranchOptionResponse(
                branch_id=m.branch_id,
                branch_name=m.branch_name,
                company_id=m.company_id,
                company_name=m.company_name,
                role_code=m.role_code,
                role_name=m.role_name,
                is_default=m.is_default
            )
            for m in memberships
        ]

        # 3. Una sola sucursal: acceso directo
        if len(memberships) == 1:

            membership = memberships[0]

            token = create_access_token({
                "sub": str(user.id),
                "company_id": str(membership.company_id),
                "branch_id": str(membership.branch_id),
                "role_code": membership.role_code,
                "scope": "branch"
            })

            return LoginResponse(
                access_token=token,
                memberships=options
            )

        # 4. Varias sucursales: token temporal
        selection_token = create_access_token(
            {
                "sub": str(user.id),
                "scope": "branch_selection"
                
            },
            expires_minutes=5,
            token_type="branch_selection"
        )

        return LoginResponse(
            selection_token=selection_token,
            requires_branch_selection=True,
            memberships=options
        )
