
from uuid import UUID

from fastapi import HTTPException

from app.core.pagination import (
    build_paginated_response,
    normalize_pagination,
)
from app.core.security import hash_password
from app.infrastructure.repositories.user_repository import UserRepository
from app.interfaces.schemas.user_schema import (
    AssignBranchUserRequest,
    AssignRoleRequest,
    SetBranchUserStatusRequest,
    UpdateBranchRoleRequest,
    UserCreateRequest,
    UserResponse,
    UserStatusRequest,
    UserUpdateRequest,
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

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


# =========================================================
# CREACIÓN DE USUARIOS
# =========================================================

class CreateUserUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        data: UserCreateRequest,
        actor: dict
    ) -> UserResponse:

        scope = actor.get("scope")

        if scope == "platform" and actor.get("role_code") == "super_admin":
            branch_id = data.branch_id

            if not branch_id:
                raise HTTPException(
                    status_code=400,
                    detail="Debe seleccionar una sucursal"
                )

        elif scope == "branch" and actor.get("role_code") == "admin":
            branch_id = UUID(str(actor["branch_id"]))

            if data.branch_id and data.branch_id != branch_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puede asignar usuarios a otra sucursal"
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="Contexto no válido"
            )

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


# =========================================================
# CONSULTA DE USUARIOS
# =========================================================

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
            raise HTTPException(
                401,
                "No se encontró el contexto del usuario"
            )

        page, page_size, skip = normalize_pagination(page, page_size)

        scope = actor.get("scope")

        # Super administrador: consulta global
        if scope == "platform":
            items = [
                _to_response(e)
                for e in self._repo.get_all(
                    skip=skip,
                    limit=page_size
                )
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
            raise HTTPException(
                403,
                "No tienes permiso para consultar usuarios"
            )

        return build_paginated_response(
            items,
            total,
            page,
            page_size
        )


class GetUserUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        actor: dict
    ) -> UserResponse:

        scope = actor.get("scope")

        if scope == "platform":
            entity = self._repo.get_by_id(user_id)

        elif scope == "branch":
            branch_id = UUID(str(actor.get("branch_id")))

            entity = self._repo.get_by_id_in_branch(
                user_id=user_id,
                branch_id=branch_id
            )

        else:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para consultar usuarios"
            )

        if not entity:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return _to_response(entity)


# =========================================================
# ACTUALIZACIÓN DE USUARIOS
# =========================================================

class UpdateUserUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: UserUpdateRequest,
        actor: dict
    ) -> UserResponse:

        scope = actor.get("scope")

        fields = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "dni": data.dni,
        }

        if scope == "platform":
            entity = self._repo.update(
                user_id,
                **fields
            )

        elif scope == "branch":
            branch_id = UUID(str(actor.get("branch_id")))

            entity = self._repo.update_in_branch(
                user_id=user_id,
                branch_id=branch_id,
                **fields
            )

        else:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para actualizar usuarios"
            )

        if not entity:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return _to_response(entity)


# =========================================================
# ESTADO GLOBAL DEL USUARIO
# =========================================================

class SetUserStatusUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: UserStatusRequest,
        actor: dict
    ) -> dict:

        if (
            actor.get("scope") != "platform"
            or actor.get("role_code") != "super_admin"
        ):
            raise HTTPException(
                status_code=403,
                detail="Solo el Super Admin puede cambiar el estado global de una cuenta"
            )

        ok = self._repo.set_active(
            user_id,
            data.is_active
        )

        if not ok:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return {
            "detail": (
                "Usuario activado"
                if data.is_active
                else "Usuario desactivado"
            ),
            "is_active": data.is_active,
        }


# =========================================================
# ROLES GLOBALES
# =========================================================

class AssignRoleUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: AssignRoleRequest,
        actor: dict
    ) -> dict:

        if (
            actor.get("scope") != "platform"
            or actor.get("role_code") != "super_admin"
        ):
            raise HTTPException(
                status_code=403,
                detail="Solo el Super Admin puede asignar roles globales"
            )

        if not self._repo.get_by_id(user_id):
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if data.role_code != "super_admin":
            raise HTTPException(
                status_code=400,
                detail="Esta operación solo permite asignar roles globales"
            )

        ok = self._repo.assign_role(
            user_id,
            data.role_code
        )

        if ok is None:
            raise HTTPException(
                status_code=404,
                detail="Rol global no encontrado"
            )

        if not ok:
            raise HTTPException(
                status_code=409,
                detail="El usuario tiene una asignación incompatible o un rol global diferente"
            )

        return {
            "detail": "Rol global asignado correctamente"
        }


# =========================================================
# ASIGNACIÓN DE USUARIOS A SUCURSALES
# =========================================================

class AssignUserToBranchUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: AssignBranchUserRequest,
        actor: dict
    ):

        scope = actor.get("scope")
        role_actor = actor.get("role_code")

        # 1. Determinar la sucursal según el actor
        if scope == "platform" and role_actor == "super_admin":
            branch_id = data.branch_id

        elif scope == "branch" and role_actor == "admin":
            branch_id = UUID(str(actor["branch_id"]))

            if data.branch_id != branch_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puede asignar usuarios a otra sucursal"
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para asignar usuarios"
            )

        # 2. Comprobar que el usuario exista
        user = self._repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar un usuario desactivado"
            )

        # 3. Un Super Admin no puede tener roles operativos
        if user.role_code == "super_admin":
            raise HTTPException(
                status_code=400,
                detail="Un Super Admin no puede pertenecer a una sucursal"
            )

        # 4. Comprobar que la sucursal y su empresa estén activas
        branch = self._repo.get_assignable_branch(branch_id)

        if not branch:
            raise HTTPException(
                status_code=404,
                detail="Sucursal no encontrada o empresa inactiva"
            )

        # 5. Crear la asignación
        result = self._repo.assign_branch_role(
            user_id=user_id,
            branch_id=branch_id,
            role_code=data.role_code
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Rol no encontrado"
            )

        if not result:
            raise HTTPException(
                status_code=409,
                detail="El usuario ya tiene una asignación en esta sucursal"
            )

        return {
            "detail": "Usuario asignado a la sucursal correctamente",
            "user_id": user_id,
            "branch_id": branch_id,
            "role_code": data.role_code
        }


# =========================================================
# ACTUALIZACIÓN DE ROLES POR SUCURSAL
# =========================================================

class UpdateBranchRoleUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: UpdateBranchRoleRequest,
        actor: dict
    ):

        scope = actor.get("scope")
        actor_role = actor.get("role_code")

        # Determinar la sucursal permitida
        if scope == "platform" and actor_role == "super_admin":
            branch_id = data.branch_id

        elif scope == "branch" and actor_role == "admin":
            branch_id = UUID(str(actor["branch_id"]))

            if data.branch_id != branch_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puede modificar usuarios de otra sucursal"
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para cambiar roles"
            )

        # No permitir super_admin como rol operativo
        if data.role_code == "super_admin":
            raise HTTPException(
                status_code=400,
                detail="No se puede asignar super_admin como rol de sucursal"
            )

        # Comprobar que el usuario exista
        user = self._repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="El usuario está desactivado"
            )

        if user.role_code == "super_admin":
            raise HTTPException(
                status_code=400,
                detail="No se puede modificar el rol de un Super Admin en una sucursal"
            )

        # Actualizar la asignación
        result = self._repo.update_branch_role(
            user_id=user_id,
            branch_id=branch_id,
            role_code=data.role_code
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Rol no encontrado"
            )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No existe una asignación activa en esta sucursal"
            )

        return {
            "detail": "Rol de sucursal actualizado correctamente",
            "user_id": user_id,
            "branch_id": branch_id,
            "role_code": data.role_code
        }


# =========================================================
# ESTADO DE ASIGNACIONES POR SUCURSAL
# =========================================================

class SetBranchUserStatusUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(
        self,
        user_id: UUID,
        data: SetBranchUserStatusRequest,
        actor: dict
    ):

        scope = actor.get("scope")
        actor_role = actor.get("role_code")

        # Determinar la sucursal permitida
        if scope == "platform" and actor_role == "super_admin":
            branch_id = data.branch_id

        elif scope == "branch" and actor_role == "admin":
            branch_id = UUID(str(actor["branch_id"]))

            if data.branch_id != branch_id:
                raise HTTPException(
                    status_code=403,
                    detail="No puede modificar el acceso a otra sucursal"
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para modificar accesos"
            )

        # Comprobar que el usuario exista
        user = self._repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="No se puede modificar el acceso de un usuario desactivado"
            )

        if user.role_code == "super_admin":
            raise HTTPException(
                status_code=400,
                detail="Un Super Admin no puede tener asignaciones de sucursal"
            )

        # Actualizar el estado de la asignación
        result = self._repo.set_branch_active(
            user_id=user_id,
            branch_id=branch_id,
            is_active=data.is_active
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No existe una asignación para este usuario en la sucursal"
            )

        action = "activado" if data.is_active else "desactivado"

        return {
            "detail": f"Acceso a la sucursal {action} correctamente",
            "user_id": user_id,
            "branch_id": branch_id,
            "is_active": data.is_active
        }
