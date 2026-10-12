from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.user_schema import (
    UserCreateRequest, 
    UserUpdateRequest, 
    AssignRoleRequest, 
    UserResponse
)
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.security import hash_password


def _to_response(entity) -> UserResponse:
    return UserResponse(
        id=entity.id,
        email=entity.email,
        first_name=entity.first_name,
        last_name=entity.last_name,
        phone=entity.phone,
        dni=entity.dni,
        is_active=entity.is_active,
        role_name=entity.role_name,
        role_code=entity.role_code,
    )


class CreateUserUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, data: UserCreateRequest) -> UserResponse:
        if self._repo.email_exists(data.email):
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        entity = self._repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            dni=data.dni,
        )
        return _to_response(entity)


class ListUsersUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, skip: int = 0, limit: int = 50) -> list[UserResponse]:
        return [_to_response(e) for e in self._repo.get_all(skip, limit)]


class GetUserUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, user_id: UUID) -> UserResponse:
        entity = self._repo.get_by_id(user_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return _to_response(entity)


class UpdateUserUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, user_id: UUID, data: UserUpdateRequest) -> UserResponse:
        entity = self._repo.update(
            user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            dni=data.dni,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return _to_response(entity)


class DeactivateUserUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, user_id: UUID) -> dict:
        ok = self._repo.deactivate(user_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"detail": "Usuario desactivado"}


class AssignRoleUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, user_id: UUID, data: AssignRoleRequest) -> dict:
        # Verificar que el usuario existe
        if not self._repo.get_by_id(user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        ok = self._repo.assign_role(user_id, data.role_code)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Rol '{data.role_code}' no existe")

        return {"detail": f"Rol '{data.role_code}' asignado correctamente"}