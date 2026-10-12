from fastapi import HTTPException

from app.interfaces.schemas.auth_schema import LoginRequest, TokenResponse
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token

_INVALID  = HTTPException(status_code=401, detail="Credenciales inválidas")
_INACTIVE = HTTPException(status_code=403, detail="Usuario inactivo")


class LoginUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, data: LoginRequest) -> TokenResponse:
        user = self._repo.get_by_email(data.email)

        # Una sola rama: no revelar si el email existe o no
        if not user or not verify_password(data.password, user.password):
            raise _INVALID

        if not user.is_active:
            raise _INACTIVE

        token = create_access_token({
            "sub":       str(user.id),
            "role_code": user.role_code,
        })
        return TokenResponse(access_token=token)