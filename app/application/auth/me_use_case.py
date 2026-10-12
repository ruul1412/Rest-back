from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.auth_schema import MeResponse
from app.infrastructure.repositories.user_repository import UserRepository


class MeUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, user_id: UUID) -> MeResponse:
        user = self._repo.get_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return MeResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role_name=user.role_name,
            role_code=user.role_code,
            is_active=user.is_active,
        )