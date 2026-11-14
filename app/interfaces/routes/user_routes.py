from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.interfaces.schemas.user_schema import (
    UserCreateRequest, UserUpdateRequest, AssignRoleRequest, UserResponse,UserStatusRequest
)
from app.application.user.user_use_cases import (
    CreateUserUseCase, ListUsersUseCase, GetUserUseCase,
    UpdateUserUseCase, AssignRoleUseCase,AssignRoleRequest, SetUserStatusUseCase
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.unit_of_work import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


# Todas las rutas requieren rol admin
_admin = Depends(require_roles(["admin"]))


def _repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@route_message("Usuario creado correctamente")
@router.post("", response_model=UserResponse, status_code=201, dependencies=[_admin])
def create_user(data: UserCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateUserUseCase(uow.users).execute(data)
    uow.commit()
    return result


@route_message("Usuarios obtenidos correctamente")
@router.get("", dependencies=[_admin])
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    repo: UserRepository = Depends(_repo),
):
    return ListUsersUseCase(repo).execute(page=page, page_size=page_size)


@route_message("Usuario obtenido correctamente")
@router.get("/{user_id}", response_model=UserResponse, dependencies=[_admin])
def get_user(user_id: UUID, repo: UserRepository = Depends(_repo)):
    return GetUserUseCase(repo).execute(user_id)


@route_message("Usuario actualizado correctamente")
@router.put("/{user_id}", response_model=UserResponse, dependencies=[_admin])
def update_user(user_id: UUID, data: UserUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateUserUseCase(uow.users).execute(user_id, data)
    uow.commit()
    return result
 
 
@route_message("Estado del usuario actualizado correctamente")
@router.patch("/{user_id}/status", dependencies=[_admin])
def set_user_status(user_id: UUID, data: UserStatusRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = SetUserStatusUseCase(uow.users).execute(user_id, data)
    uow.commit()
    return result
 
 
@route_message("Rol asignado correctamente")
@router.post("/{user_id}/role", dependencies=[_admin])
def assign_role(user_id: UUID, data: AssignRoleRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = AssignRoleUseCase(uow.users).execute(user_id, data)
    uow.commit()
    return result