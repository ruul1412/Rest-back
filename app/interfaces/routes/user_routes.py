from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.user_schema import (
    UserCreateRequest, UserUpdateRequest, AssignRoleRequest, UserResponse
)
from app.application.user.user_use_cases import (
    CreateUserUseCase, ListUsersUseCase, GetUserUseCase,
    UpdateUserUseCase, DeactivateUserUseCase, AssignRoleUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])

# Todas las rutas requieren rol admin
_admin = Depends(require_roles(["admin"]))


def _repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post("", response_model=UserResponse, status_code=201, dependencies=[_admin])
def create_user(data: UserCreateRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    result = CreateUserUseCase(repo).execute(data)
    db.commit()
    return result


@router.get("", response_model=list[UserResponse], dependencies=[_admin])
def list_users(skip: int = 0, limit: int = 50, repo: UserRepository = Depends(_repo)):
    return ListUsersUseCase(repo).execute(skip, limit)


@router.get("/{user_id}", response_model=UserResponse, dependencies=[_admin])
def get_user(user_id: UUID, repo: UserRepository = Depends(_repo)):
    return GetUserUseCase(repo).execute(user_id)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[_admin])
def update_user(user_id: UUID, data: UserUpdateRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    result = UpdateUserUseCase(repo).execute(user_id, data)
    db.commit()
    return result
 
 
@router.delete("/{user_id}", dependencies=[_admin])
def deactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    result = DeactivateUserUseCase(repo).execute(user_id)
    db.commit()
    return result
 
 
@router.post("/{user_id}/role", dependencies=[_admin])
def assign_role(user_id: UUID, data: AssignRoleRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    result = AssignRoleUseCase(repo).execute(user_id, data)
    db.commit()
    return result