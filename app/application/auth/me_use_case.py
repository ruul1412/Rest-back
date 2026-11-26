from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.auth_schema import MeResponse
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.user.user_entity import UserEntity


class MeUseCase:

    def __init__(self, repo: UserRepository):
        self._repo = repo

    def execute(self, user: UserEntity, payload: dict) -> MeResponse:

        scope = payload.get("scope")
        role_code = payload.get("role_code")

        # 1. Super administrador: contexto global
        if scope == "platform":

            if role_code != "super_admin":
                raise HTTPException(
                    status_code=403,
                    detail="Contexto de plataforma no autorizado"
                )

            return MeResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                scope=scope,
                role_code=role_code,
                role_name=user.role_name,
                is_active=user.is_active,
            )

        # 2. Usuario de sucursal
        if scope == "branch":

            branch_id = payload.get("branch_id")

            if not branch_id:
                raise HTTPException(
                    status_code=401,
                    detail="El token no contiene una sucursal"
                )

            membership = self._repo.get_active_membership(
                user.id,
                UUID(str(branch_id))
            )

            if not membership:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes acceso activo a esta sucursal"
                )

            return MeResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                scope=scope,
                role_code=membership.role_code,
                role_name=membership.role_name,
                company_id=membership.company_id,
                company_name=membership.company_name,
                branch_id=membership.branch_id,
                branch_name=membership.branch_name,
                is_active=user.is_active,
            )

        raise HTTPException(
            status_code=401,
            detail="Contexto de autenticación inválido"
        )