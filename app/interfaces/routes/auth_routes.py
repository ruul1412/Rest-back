
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.infrastructure.repositories.user_repository import UserRepository

from app.interfaces.dependencies.auth_dependencies import get_current_user

from app.interfaces.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    SelectBranchRequest,
    TokenResponse,
    MeResponse
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.application.auth.me_use_case import MeUseCase
from app.application.auth.login_use_case import LoginUseCase
from app.application.auth.select_branch_use_case import SelectBranchUseCase

from app.domain.user.user_entity import UserEntity


router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()

@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    return LoginUseCase(UserRepository(db)).execute(data)


@router.post("/select-branch", response_model=TokenResponse)
def select_branch(
    data: SelectBranchRequest,
    db: Session = Depends(get_db),
):
    return SelectBranchUseCase(UserRepository(db)).execute(data)


@router.get("/me", response_model=MeResponse)
def me(
    current_user: UserEntity = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)

    return MeUseCase(
        UserRepository(db)
    ).execute(current_user, payload)
