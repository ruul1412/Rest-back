
from typing import Optional
from uuid import UUID
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.domain.user.branch_user_entity import BranchUserEntity
from app.domain.user.user_entity import UserEntity, BranchAssignmentEntity
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
        is_deleted=model.is_deleted,
        role_code=role_code,
        role_name=role_name,
    )


def _to_platform_entity(model: UserModel) -> UserEntity:
    entity = _to_entity(model)

    entity.assignments = [
        BranchAssignmentEntity(
            branch_id=membership.branch_id,
            branch_name=membership.branch.name,
            company_name=(
                membership.branch.company.name
                if membership.branch.company
                else None
            ),
            role_code=(
                membership.role.code
                if membership.role
                else None
            ),
            role_name=(
                membership.role.name
                if membership.role
                else None
            ),
            is_active=membership.is_active,
            is_deleted=membership.is_deleted,
        )
        for membership in model.branch_users
    ]

    return entity


def _to_branch_entity(
    model: UserModel,
    branch_id: UUID
) -> UserEntity:

    entity = _to_entity(model)

    membership = next(
        (
            bu for bu in model.branch_users
            if bu.branch_id == branch_id
            and not bu.is_deleted
        ),
        None
    )

    if membership:
        entity.branch_is_active = membership.is_active
        entity.branch_is_deleted = membership.is_deleted

        if membership.role:
            entity.role_code = membership.role.code
            entity.role_name = membership.role.name

    return entity

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
                UserModel.is_deleted.is_(False),
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_deleted.is_(False)
            )
            .first()
        )

        if not model:
            return None

        return _to_branch_entity(model, branch_id)

    def count(self) -> int:
        return self._db.query(UserModel.id).count()

   
    def get_all(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> list[UserEntity]:

        models = (
            self._base_query()
            .options(
                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.branch)
                .joinedload(BranchModel.company),

                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.role)
            )
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [
            _to_platform_entity(model)
            for model in models
        ]

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
                UserModel.is_active.is_(True),
                UserModel.is_deleted.is_(False),
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True),
                BranchUserModel.is_deleted.is_(False)
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

        return _to_branch_entity(model, branch_id)

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

        # Verificar que el usuario exista y esté activo
        user = (
            self._db.query(UserModel)
            .filter(
                UserModel.id == user_id,
                UserModel.is_active.is_(True),
                UserModel.is_deleted.is_(False)
            )
            .first()
        )

        if not user:
            return False

        # No permitir roles globales como roles de sucursal
        if role_code == "super_admin":
            return False

        # Buscar el rol operativo
        role = (
            self._db.query(RoleModel)
            .filter(
                RoleModel.code == role_code,
                RoleModel.is_deleted.is_(False)
            )
            .first()
        )

        if not role:
            return None

        # Buscar una asignación existente, incluso si fue eliminada
        membership = (
            self._db.query(BranchUserModel)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.branch_id == branch_id
            )
            .first()
        )

        if membership:
            # No duplicar una asignación que ya está activa
            if (
                membership.is_active
                and not membership.is_deleted
            ):
                return False

            # Recuperar y reactivar la asignación
            membership.role_id = role.id
            membership.is_deleted = False
            membership.is_active = True

            self._db.flush()

            return True

        # Crear una asignación nueva
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

        user = (
            self._db.query(UserModel)
            .filter(
                UserModel.id == user_id,
                UserModel.is_active.is_(True),
                UserModel.is_deleted.is_(False)
            )
            .first()
        )

        if not user:
            return False

        membership = (
            self._db.query(BranchUserModel)
            .filter(
                BranchUserModel.user_id == user_id,
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_active.is_(True),
                BranchUserModel.is_deleted.is_(False)
            )
            .first()
        )

        if not membership:
            return False

        if role_code == "super_admin":
            return False

        role = (
            self._db.query(RoleModel)
            .filter(
                RoleModel.code == role_code,
                RoleModel.is_deleted.is_(False)
            )
            .first()
        )

        if not role:
            return None

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
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_deleted.is_(False)
            )
            .first()
        )

        if not membership:
            return False

        # No permitir reactivar una asignación
        # si la cuenta global está inactiva o eliminada
        if is_active:
            user = (
                self._db.query(UserModel)
                .filter(
                    UserModel.id == user_id,
                    UserModel.is_active.is_(True),
                    UserModel.is_deleted.is_(False)
                )
                .first()
            )

            if not user:
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
                BranchUserModel.is_active.is_(True),
                BranchUserModel.is_deleted.is_(False),

                BranchModel.is_active.is_(True),
                BranchModel.is_deleted.is_(False),

                CompanyModel.is_active.is_(True),
                CompanyModel.is_deleted.is_(False),

                RoleModel.is_deleted.is_(False),
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
                user_id=m.user_id,
                branch_id=m.branch_id,
                branch_name=m.branch.name,
                company_id=m.branch.company.id,
                company_name=m.branch.company.name,
                role_id=m.role_id,
                role_code=m.role.code,
                role_name=m.role.name,
                is_default=m.is_default
            )
            for m in memberships
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
                BranchUserModel.is_active.is_(True),
                BranchUserModel.is_deleted.is_(False),

                BranchModel.is_active.is_(True),
                BranchModel.is_deleted.is_(False),

                CompanyModel.is_active.is_(True),
                CompanyModel.is_deleted.is_(False),

                RoleModel.is_deleted.is_(False),
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
    
    # -----------------------------------------------------
    # LISTADOS Y CONTEOS POR SUCURSAL
    # -----------------------------------------------------

    def get_all_by_branch(
        self,
        branch_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> list[UserEntity]:

        query = (
            self._base_query()
            .join(UserModel.branch_users)
            .options(
                joinedload(UserModel.branch_users)
                .joinedload(BranchUserModel.role)
            )
            .filter(
                UserModel.is_deleted.is_(False),
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_deleted.is_(False),
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )

        users = query.all()

        return [
            _to_branch_entity(user, branch_id)
            for user in users
        ]
    
    def count_by_branch(self, branch_id: UUID) -> int:

        return (
            self._db.query(UserModel.id)
            .join(UserModel.branch_users)
            .filter(
                UserModel.is_deleted.is_(False),
                BranchUserModel.branch_id == branch_id,
                BranchUserModel.is_deleted.is_(False),
            )
            .distinct()
            .count()
        )

    def search_assignable_users(
        self,
        query: str,
        branch_id: UUID,
        limit: int = 10
    ) -> list[UserEntity]:

        term = f"%{query.strip()}%"

        # Obtener la empresa de la sucursal destino
        branch = (
            self._db.query(BranchModel)
            .filter(BranchModel.id == branch_id)
            .first()
        )

        if not branch:
            return []

        company_id = branch.company_id

        users = (
            self._base_query()
            .filter(
                UserModel.is_active.is_(True),
                UserModel.is_deleted.is_(False),

                or_(
                    UserModel.email.ilike(term),
                    UserModel.first_name.ilike(term),
                    UserModel.last_name.ilike(term),
                ),

                # Excluir cuentas super_admin
                ~UserModel.user_roles.has(
                    UserRoleModel.role.has(
                        RoleModel.code == "super_admin"
                    )
                ),

                # Excluir usuarios ya asignados a esta sucursal
                ~UserModel.branch_users.any(
                    and_(
                        BranchUserModel.branch_id == branch_id,
                        BranchUserModel.is_deleted.is_(False)
                    )
                ),

                # Excluir usuarios que pertenezcan a otra empresa
                ~UserModel.branch_users.any(
                    and_(
                        BranchUserModel.is_deleted.is_(False),
                        BranchUserModel.branch.has(
                            BranchModel.company_id != company_id
                        )
                    )
                )
            )
            .order_by(
                UserModel.first_name.asc(),
                UserModel.last_name.asc()
            )
            .limit(limit)
            .all()
        )

        return [
            _to_entity(user)
            for user in users
        ]
    