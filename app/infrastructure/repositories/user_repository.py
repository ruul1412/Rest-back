
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.domain.user.branch_user_entity import BranchUserEntity
from app.domain.user.user_entity import UserEntity
from app.infrastructure.models.branch_model import BranchModel
from app.infrastructure.models.branch_user_model import BranchUserModel
from app.infrastructure.models.company_model import CompanyModel
from app.infrastructure.models.role_model import RoleModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.models.user_role_model import UserRoleModel


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def _to_entity(model: UserModel) -> UserEntity:
    role_code = None
    role_name = None

    # user_roles es uselist=False → objeto único, no lista
    if model.user_roles and model.user_roles.role:
        role_code = model.user_roles.role.code
        role_name = model.user_roles.role.name

    return UserEntity(
        id=model.id,
        email=model.email,
        password=model.password,
        first_name=model.first_name,
        last_name=model.last_name,
        phone=model.phone,
        dni=model.dni,
        is_active=model.is_active,
        role_code=role_code,
        role_name=role_name,
    )


# =========================================================
# USER REPOSITORY
# =========================================================

class UserRepository:

    # -----------------------------------------------------
    # INICIALIZACIÓN Y CONSULTAS BASE
    # -----------------------------------------------------

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return (
            self._db.query(UserModel)
            .options(
                joinedload(UserModel.user_roles)
                .joinedload(UserRoleModel.role)
            )
        )

    def _to_branch_entity(
        self,
        model: UserModel,
        branch_id: UUID
    ) -> UserEntity:

        entity = _to_entity(model)

        membership = next(
            (
                bu for bu in model.branch_users
                if bu.branch_id == branch_id and bu.is_active
            ),
            None
        )

        if membership and membership.role:
            entity.role_code = membership.role.code
            entity.role_name = membership.role.name

        return entity

    # -----------------------------------------------------
    # CONSULTAS DE USUARIOS
    # -----------------------------------------------------

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        model = (
            self._base_query()
            .filter(UserModel.email == email)
            .first()
        )

        return _to_entity(model) if model else None

    def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        model = (
            self._base_query()
            .filter(UserModel.id == user_id)
            .first()
        )

        return _to_entity(model) if model else None

    def get_by_id_in_branch(
        self,
        user_id: UUID,
        branch_id: UUID
    ) -> Optional[UserEntity]:

        model = (
            self._base_query()
            .options(
                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.role)
            )
            .join(
                BranchUserModel,
                BranchUserModel.user_id == UserModel.id
            )
            .filter(
                UserModel.id == user_id,
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .first()
        )

        if not model:
            return None

        return self._to_branch_entity(model, branch_id)

    def count(self) -> int:
        return self._db.query(UserModel.id).count()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> list[UserEntity]:

        models = (
            self._base_query()
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [_to_entity(m) for m in models]

    def email_exists(self, email: str) -> bool:
        return (
            self._db.query(UserModel.id)
            .filter(UserModel.email == email)
            .first()
            is not None
        )

    # -----------------------------------------------------
    # CREACIÓN Y ACTUALIZACIÓN DE USUARIOS
    # -----------------------------------------------------

    def create(
        self,
        email: str,
        hashed_password: str,
        **kwargs
    ) -> UserEntity:

        model = UserModel(
            email=email,
            password=hashed_password,
            **kwargs
        )

        self._db.add(model)
        self._db.flush()
        self._db.refresh(model)

        return _to_entity(model)

    def update(
        self,
        user_id: UUID,
        **fields
    ) -> Optional[UserEntity]:

        model = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )

        if not model:
            return None

        for key, value in fields.items():
            if value is not None:
                setattr(model, key, value)

        self._db.flush()
        self._db.refresh(model)

        return _to_entity(model)

    def update_in_branch(
        self,
        user_id: UUID,
        branch_id: UUID,
        **fields
    ) -> Optional[UserEntity]:

        model = (
            self._base_query()
            .options(
                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.role)
            )
            .join(
                BranchUserModel,
                BranchUserModel.user_id == UserModel.id
            )
            .filter(
                UserModel.id == user_id,
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .first()
        )

        if not model:
            return None

        for key, value in fields.items():
            if value is not None:
                setattr(model, key, value)

        self._db.flush()
        self._db.refresh(model)

        return self._to_branch_entity(model, branch_id)

    # -----------------------------------------------------
    # ESTADO GLOBAL DEL USUARIO
    # -----------------------------------------------------

    def deactivate(self, user_id: UUID) -> bool:
        """Soft delete — solo marca is_active=False."""

        model = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )

        if not model:
            return False

        model.is_active = False

        self._db.flush()

        return True

    def set_active(
        self,
        user_id: UUID,
        is_active: bool
    ) -> bool:
        """Activa o desactiva (soft delete) un usuario."""

        model = (
            self._db.query(UserModel)
            .filter(UserModel.id == user_id)
            .first()
        )

        if not model:
            return False

        model.is_active = is_active

        self._db.flush()

        return True

    # -----------------------------------------------------
    # ROLES GLOBALES
    # -----------------------------------------------------

    def assign_role(
        self,
        user_id: UUID,
        role_code: str
    ) -> Optional[bool]:

        # Solo se permiten roles globales autorizados
        if role_code != "super_admin":
            return None

        role = (
            self._db.query(RoleModel)
            .filter(RoleModel.code == role_code)
            .first()
        )

        if not role:
            return None

        # Un Super Admin no debe tener asignaciones operativas
        has_memberships = (
            self._db.query(BranchUserModel)
            .filter(BranchUserModel.user_id == user_id)
            .first()
        )

        if has_memberships:
            return False

        existing = (
            self._db.query(UserRoleModel)
            .filter(UserRoleModel.user_id == user_id)
            .first()
        )

        if existing:
            # No reemplazar un rol global existente
            if existing.role_id == role.id:
                return True

            return False

        self._db.add(
            UserRoleModel(
                user_id=user_id,
                role_id=role.id
            )
        )

        self._db.flush()

        return True

    # -----------------------------------------------------
    # ASIGNACIONES Y ROLES POR SUCURSAL
    # -----------------------------------------------------

    def assign_branch_role(
        self,
        user_id: UUID,
        branch_id: UUID,
        role_code: str
    ) -> Optional[bool]:

        # Evitar duplicar o modificar una asignación existente
        existing = (
            self._db.query(BranchUserModel)
            .filter_by(
                user_id=user_id,
                branch_id=branch_id
            )
            .first()
        )

        if existing:
            return False

        # Buscar el rol solicitado
        role = (
            self._db.query(RoleModel)
            .filter(RoleModel.code == role_code)
            .first()
        )

        if not role:
            return None

        # Crear una nueva asignación
        membership = BranchUserModel(
            user_id=user_id,
            branch_id=branch_id,
            role_id=role.id,
            is_active=True,
            is_default=False
        )

        self._db.add(membership)
        self._db.flush()

        return True

    def update_branch_role(
        self,
        user_id: UUID,
        branch_id: UUID,
        role_code: str
    ) -> Optional[bool]:

        # Buscar la asignación activa del usuario en esa sucursal
        membership = (
            self._db.query(BranchUserModel)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .first()
        )

        if not membership:
            return False

        # Buscar el nuevo rol
        role = (
            self._db.query(RoleModel)
            .filter(RoleModel.code == role_code)
            .first()
        )

        if not role:
            return None

        # Actualizar solamente el rol de esta sucursal
        membership.role_id = role.id

        self._db.flush()

        return True

    def set_branch_active(
        self,
        user_id: UUID,
        branch_id: UUID,
        is_active: bool
    ) -> bool:

        membership = (
            self._db.query(BranchUserModel)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.branch_id == branch_id
            )
            .first()
        )

        if not membership:
            return False

        membership.is_active = is_active

        self._db.flush()

        return True

    # -----------------------------------------------------
    # CONSULTAS DE MEMBRESÍAS Y SUCURSALES
    # -----------------------------------------------------

    def get_active_memberships(
        self,
        user_id: UUID
    ) -> list[BranchUserEntity]:

        memberships = (
            self._db.query(BranchUserModel)
            .join(BranchUserModel.branch)
            .join(BranchModel.company)
            .join(BranchUserModel.role)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.is_active == True
            )
            .order_by(
                BranchUserModel.is_default.desc(),
                CompanyModel.name,
                BranchModel.name
            )
            .all()
        )

        return [
            BranchUserEntity(
                user_id=membership.user_id,
                branch_id=membership.branch_id,
                branch_name=membership.branch.name,
                company_id=membership.branch.company.id,
                company_name=membership.branch.company.name,
                role_id=membership.role_id,
                role_code=membership.role.code,
                role_name=membership.role.name,
                is_default=membership.is_default
            )
            for membership in memberships
        ]

    def get_active_membership(
        self,
        user_id: UUID,
        branch_id: UUID
    ) -> Optional[BranchUserEntity]:

        membership = (
            self._db.query(BranchUserModel)
            .join(BranchUserModel.branch)
            .join(BranchModel.company)
            .join(BranchUserModel.role)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .first()
        )

        if not membership:
            return None

        return BranchUserEntity(
            user_id=membership.user_id,
            branch_id=membership.branch_id,
            branch_name=membership.branch.name,
            company_id=membership.branch.company.id,
            company_name=membership.branch.company.name,
            role_id=membership.role_id,
            role_code=membership.role.code,
            role_name=membership.role.name,
            is_default=membership.is_default
        )

    def get_assignable_branch(
        self,
        branch_id: UUID
    ) -> Optional[BranchModel]:

        return (
            self._db.query(BranchModel)
            .join(BranchModel.company)
            .filter(
                BranchModel.id == branch_id,
                CompanyModel.is_active.is_(True)
            )
            .first()
        )

    # -----------------------------------------------------
    # LISTADOS Y CONTEOS POR SUCURSAL
    # -----------------------------------------------------

    def get_all_by_branch(
        self,
        branch_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> list[UserEntity]:

        models = (
            self._base_query()
            .options(
                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.role)
            )
            .join(
                BranchUserModel,
                BranchUserModel.user_id == UserModel.id
            )
            .filter(
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        entities = []

        for model in models:
            entity = _to_entity(model)

            membership = next(
                (
                    bu for bu in model.branch_users
                    if bu.branch_id == branch_id and bu.is_active
                ),
                None
            )

            if membership and membership.role:
                entity.role_code = membership.role.code
                entity.role_name = membership.role.name

            entities.append(entity)

        return entities

    def count_by_branch(self, branch_id: UUID) -> int:

        return (
            self._db.query(UserModel.id)
            .join(
                BranchUserModel,
                BranchUserModel.user_id == UserModel.id
            )
            .filter(
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True)
            )
            .count()
        )
