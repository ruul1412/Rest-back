from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.interfaces.dependencies.auth_dependencies import get_current_user
from app.interfaces.schemas.auth_schema import LoginRequest, TokenResponse, MeResponse
from app.application.auth.me_use_case import MeUseCase
from app.application.auth.login_use_case import LoginUseCase
from app.domain.user.user_entity import UserEntity

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    return LoginUseCase(UserRepository(db)).execute(data)

@router.get("/me", response_model=MeResponse)
def me(
    current_user: UserEntity = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MeUseCase(UserRepository(db)).execute(current_user.id)