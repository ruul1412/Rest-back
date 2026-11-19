from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.user_schema import (
    UserCreateRequest, 
    UserUpdateRequest, 
    AssignRoleRequest, 
    UserResponse,UserStatusRequest
)
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.pagination import build_paginated_response, normalize_pagination
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


# class CreateUserUseCase:
#     def __init__(self, repo: UserRepository): self._repo = repo

#     def execute(self, data: UserCreateRequest) -> UserResponse:
#         if self._repo.email_exists(data.email):
#             raise HTTPException(status_code=400, detail="El email ya está registrado")

#         entity = self._repo.create(
#             email=data.email,
#             hashed_password=hash_password(data.password),
#             first_name=data.first_name,
#             last_name=data.last_name,
#             phone=data.phone,
#             dni=data.dni,
#         )
#         return _to_response(entity)

class CreateUserUseCase:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, data: UserCreateRequest, actor: dict) -> UserResponse:

        scope = actor.get("scope")

        if scope == "platform":
            branch_id = data.branch_id

            if not branch_id:
                raise HTTPException(
                    status_code=400,
                    detail="Debe seleccionar una sucursal"
                )

        elif scope == "branch":
            branch_id = UUID(actor["branch_id"])

            if data.branch_id and data.branch_id != branch_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puede asignar usuarios a otra sucursal"
                )
        else:
            raise HTTPException(status_code=403, detail="Contexto no válido")

        if data.role_code == "super_admin":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar super_admin como rol de sucursal"
            )

        branch = self._repo.get_assignable_branch(branch_id)

        if not branch:
            raise HTTPException(
                status_code=404,
                detail="Sucursal no encontrada o empresa inactiva"
            )

        user = self._repo.get_by_email(data.email)

        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="El usuario está desactivado"
                )

            user_id = user.id

        else:
            if not data.password:
                raise HTTPException(
                    status_code=400,
                    detail="La contraseña es obligatoria para crear un usuario"
                )

            user = self._repo.create(
                email=data.email,
                hashed_password=hash_password(data.password),
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone,
                dni=data.dni,
            )

            user_id = user.id

        ok = self._repo.assign_branch_role(
            user_id=user_id,
            branch_id=branch_id,
            role_code=data.role_code
        )

        if ok is None:
            raise HTTPException(
                status_code=404,
                detail=f"Rol '{data.role_code}' no encontrado"
            )

        if not ok:
            raise HTTPException(
                status_code=409,
                detail="El usuario ya tiene una asignación en esta sucursal"
            )

        # Obtener la membresía con el rol asignado
        membership = self._repo.get_active_membership(
            user_id,
            branch_id
        )

        if not membership:
            raise HTTPException(
                status_code=500,
                detail="No se pudo obtener la asignación del usuario"
            )

        # Recuperar la entidad del usuario
        entity = self._repo.get_by_id(user_id)

        if not entity:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        # Incorporar el rol de la sucursal a la entidad
        entity.role_code = membership.role_code
        entity.role_name = membership.role_name

        return _to_response(entity)

class ListUsersUseCase:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        page: int = 1,
        page_size: int | None = None,
        actor: dict | None = None
    ) -> dict:

        if not actor:
            raise HTTPException(401, "No se encontró el contexto del usuario")

        page, page_size, skip = normalize_pagination(page, page_size)

        scope = actor.get("scope")

        # Super administrador: consulta global
        if scope == "platform":
            items = [
                _to_response(e)
                for e in self._repo.get_all(skip=skip, limit=page_size)
            ]
            total = self._repo.count()

        # Administrador: consulta solo su sucursal
        elif scope == "branch":
            branch_id = actor.get("branch_id")

            if not branch_id:
                raise HTTPException(
                    403,
                    "No se encontró una sucursal en el contexto del usuario"
                )

            branch_id = UUID(str(branch_id))

            items = [
                _to_response(e)
                for e in self._repo.get_all_by_branch(
                    branch_id=branch_id,
                    skip=skip,
                    limit=page_size
                )
            ]

            total = self._repo.count_by_branch(branch_id)

        else:
            raise HTTPException(403, "No tienes permiso para consultar usuarios")

        return build_paginated_response(
            items, total, page, page_size
        )


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

class SetUserStatusUseCase:
    def __init__(self, repo: UserRepository): self._repo = repo

    def execute(self, user_id: UUID, data: UserStatusRequest) -> dict:
        ok = self._repo.set_active(user_id, data.is_active)
        if not ok:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {
            "detail": "Usuario activado" if data.is_active else "Usuario desactivado",
            "is_active": data.is_active,
        }

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