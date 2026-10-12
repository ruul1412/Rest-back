from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from app.infrastructure.models.permission_model import PermissionModel
from app.infrastructure.models.user_permission_model import UserPermissionModel
from app.domain.permission.permission_entity import PermissionEntity, UserPermissionEntity


def _to_entity(model: PermissionModel) -> PermissionEntity:
    return PermissionEntity(
        id=model.id,
        code=model.code,
        description=model.description,
    )


def _to_user_perm_entity(model: UserPermissionModel) -> UserPermissionEntity:
    return UserPermissionEntity(
        id=model.id,
        code=model.permission.code,
        description=model.permission.description,
        granted_by=model.granted_by,
        expires_at=model.expires_at,
        reason=model.reason,
    )


class PermissionRepository:

    def __init__(self, db: Session):
        self._db = db

    # ── Lecturas ──────────────────────────────────────────────────────────────

    def get_all(self) -> list[PermissionEntity]:
        models = self._db.query(PermissionModel).order_by(PermissionModel.code).all()
        return [_to_entity(m) for m in models]

    def get_by_code(self, code: str) -> Optional[PermissionEntity]:
        model = self._db.query(PermissionModel).filter(PermissionModel.code == code).first()
        return _to_entity(model) if model else None

    def get_by_user(self, user_id: UUID) -> list[UserPermissionEntity]:
        """
        Permisos directos activos del usuario.
        Excluye los vencidos (expires_at < ahora).
        """
        now = datetime.now(timezone.utc)
        models = (
            self._db.query(UserPermissionModel)
            .filter(UserPermissionModel.user_id == user_id)
            .filter(
                (UserPermissionModel.expires_at == None) |
                (UserPermissionModel.expires_at > now)
            )
            .all()
        )
        return [_to_user_perm_entity(m) for m in models]

    def codes_exist(self, codes: list[str]) -> tuple[bool, list[str]]:
        found = (
            self._db.query(PermissionModel.code)
            .filter(PermissionModel.code.in_(codes))
            .all()
        )
        found_codes = {row.code for row in found}
        missing = [c for c in codes if c not in found_codes]
        return (len(missing) == 0, missing)

    # ── Escrituras ────────────────────────────────────────────────────────────

    def assign_to_user(
        self,
        user_id: UUID,
        codes: list[str],
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Reemplaza todos los permisos directos del usuario por los indicados.
        Incluye granted_by, expires_at y reason para trazabilidad completa.
        Lista vacía → revoca todos.
        """
        all_exist, missing = self.codes_exist(codes)
        if not all_exist:
            return False

        # Obtener los permisos solicitados
        permission_ids: list[UUID] = []
        if codes:
            rows = (
                self._db.query(PermissionModel.id)
                .filter(PermissionModel.code.in_(codes))
                .all()
            )
            permission_ids = [row.id for row in rows]

        # Eliminar asignaciones actuales
        self._db.query(UserPermissionModel).filter(
            UserPermissionModel.user_id == user_id
        ).delete(synchronize_session=False)

        # Insertar nuevas con auditoría completa
        for perm_id in permission_ids:
            self._db.add(UserPermissionModel(
                user_id=user_id,
                permission_id=perm_id,
                granted_by=granted_by,
                expires_at=expires_at,
                reason=reason,
            ))

        self._db.flush()
        return True

    def revoke_from_user(self, user_id: UUID, code: str) -> bool:
        """Revoca un permiso directo específico del usuario."""
        perm = self._db.query(PermissionModel).filter(PermissionModel.code == code).first()
        if not perm:
            return False

        deleted = (
            self._db.query(UserPermissionModel)
            .filter(
                UserPermissionModel.user_id == user_id,
                UserPermissionModel.permission_id == perm.id,
            )
            .delete(synchronize_session=False)
        )
        self._db.flush()
        return deleted > 0

    def get_effective_codes(self, user_id: UUID) -> set[str]:
        """
        Todos los permission codes activos del usuario:
        los heredados por su rol + los directos no vencidos.
        Usado por require_permission() en auth_dependencies.
        """
        from app.infrastructure.models.role_permission_model import RolePermissionModel
        from app.infrastructure.models.user_role_model import UserRoleModel

        # 1. Permisos por rol
        role_perms = (
            self._db.query(PermissionModel.code)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .join(UserRoleModel, UserRoleModel.role_id == RolePermissionModel.role_id)
            .filter(UserRoleModel.user_id == user_id)
            .all()
        )

        # 2. Permisos directos activos
        now = datetime.now(timezone.utc)
        direct_perms = (
            self._db.query(PermissionModel.code)
            .join(UserPermissionModel, UserPermissionModel.permission_id == PermissionModel.id)
            .filter(UserPermissionModel.user_id == user_id)
            .filter(
                (UserPermissionModel.expires_at == None) |
                (UserPermissionModel.expires_at > now)
            )
            .all()
        )

        return {p.code for p in role_perms} | {p.code for p in direct_perms}