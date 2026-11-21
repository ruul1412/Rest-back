
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.user.user_use_cases import (
    AssignRoleUseCase,
    AssignUserToBranchUseCase,
    CreateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    SetBranchUserStatusUseCase,
    SetUserStatusUseCase,
    UpdateBranchRoleUseCase,
    UpdateUserUseCase,
)
from app.core.config import settings
from app.core.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.unit_of_work import UnitOfWork
from app.interfaces.dependencies.auth_dependencies import (
    require_user_management,
)
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
# CONFIGURACIÓN DEL ROUTER
# =========================================================

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func

    return decorator


# =========================================================
# DEPENDENCIAS
# =========================================================

def _repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


# =========================================================
# CONSULTA DE USUARIOS
# =========================================================

@route_message("Usuarios obtenidos correctamente")
@router.get("")
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE
    ),
    repo: UserRepository = Depends(_repo),
    actor: dict = Depends(require_user_management()),
):
    return ListUsersUseCase(repo).execute(
        page=page,
        page_size=page_size,
        actor=actor
    )


@route_message("Usuario obtenido correctamente")
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    repo: UserRepository = Depends(_repo),
    actor: dict = Depends(require_user_management())
):
    return GetUserUseCase(repo).execute(
        user_id=user_id,
        actor=actor
    )


# =========================================================
# CREACIÓN Y ACTUALIZACIÓN DE USUARIOS
# =========================================================

@route_message("Usuario creado correctamente")
@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreateRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = CreateUserUseCase(uow.users).execute(
            data,
            actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


@route_message("Usuario actualizado correctamente")
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = UpdateUserUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


# =========================================================
# ESTADO GLOBAL DEL USUARIO
# =========================================================

@route_message("Estado del usuario actualizado correctamente")
@router.patch("/{user_id}/status")
def set_user_status(
    user_id: UUID,
    data: UserStatusRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = SetUserStatusUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


# =========================================================
# ROLES GLOBALES
# =========================================================

@route_message("Rol global asignado correctamente")
@router.post("/{user_id}/role")
def assign_role(
    user_id: UUID,
    data: AssignRoleRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = AssignRoleUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


# =========================================================
# ASIGNACIONES POR SUCURSAL
# =========================================================

@route_message("Usuario asignado a la sucursal correctamente")
@router.post("/{user_id}/branches")
def assign_user_to_branch(
    user_id: UUID,
    data: AssignBranchUserRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = AssignUserToBranchUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


@route_message("Rol de sucursal actualizado correctamente")
@router.patch("/{user_id}/branches/role")
def update_branch_role(
    user_id: UUID,
    data: UpdateBranchRoleRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = UpdateBranchRoleUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise


@route_message("Acceso a sucursal actualizado correctamente")
@router.patch("/{user_id}/branches/status")
def set_branch_user_status(
    user_id: UUID,
    data: SetBranchUserStatusRequest,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_user_management())
):
    uow = UnitOfWork(db)

    try:
        result = SetBranchUserStatusUseCase(uow.users).execute(
            user_id=user_id,
            data=data,
            actor=actor
        )

        uow.commit()

        return result

    except Exception:
        uow.rollback()
        raise
