
from fastapi import HTTPException
from app.infrastructure.repositories.user_repository import (UserRepository)
from app.core.security import (
    decode_selection_token,
    create_access_token,
)

from app.interfaces.schemas.auth_schema import (
    SelectBranchRequest,
    TokenResponse
)


class SelectBranchUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, data: SelectBranchRequest) -> TokenResponse:

        # Validar el token temporal
        payload = decode_selection_token(data.selection_token)

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token de selección inválido"
            )

        # Verificar que el usuario siga activo
        user = self._repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Usuario inactivo o inexistente"
            )

        # Verificar que pertenece a la sucursal elegida
        membership = self._repo.get_active_membership(
            user.id,
            data.branch_id
        )

        if not membership:
            raise HTTPException(
                status_code=403,
                detail="No tienes acceso a esta sucursal"
            )

        # Generar token definitivo
        token = create_access_token({
            "sub": str(user.id),
            "company_id": str(membership.company_id),
            "branch_id": str(membership.branch_id),
            "role_code": membership.role_code,
            "scope": "branch"
        })

        return TokenResponse(access_token=token)
