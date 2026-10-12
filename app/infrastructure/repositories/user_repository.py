from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.models.user_role_model import UserRoleModel
from app.infrastructure.models.role_model import RoleModel
from sqlalchemy.orm import joinedload
from app.domain.user.user_entity import UserEntity

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

class UserRepository:
 
    def __init__(self, db: Session):
        self._db = db
 
    def _base_query(self):
        return (
            self._db.query(UserModel)
            .options(joinedload(UserModel.user_roles).joinedload(UserRoleModel.role))
        )
 
    # ── Lecturas ──────────────────────────────────────────────────────────────
 
    def get_by_email(self, email: str) -> Optional[UserEntity]:
        model = self._base_query().filter(UserModel.email == email).first()
        return _to_entity(model) if model else None
 
    def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        model = self._base_query().filter(UserModel.id == user_id).first()
        return _to_entity(model) if model else None
 
    def get_all(self, skip: int = 0, limit: int = 50) -> list[UserEntity]:
        models = (
            self._base_query()
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_to_entity(m) for m in models]
 
    def email_exists(self, email: str) -> bool:
        return self._db.query(UserModel.id).filter(UserModel.email == email).first() is not None
 
    # ── Escrituras ────────────────────────────────────────────────────────────
 
    def create(self, email: str, hashed_password: str, **kwargs) -> UserEntity:
        model = UserModel(email=email, password=hashed_password, **kwargs)
        self._db.add(model)
        self._db.flush()
        self._db.refresh(model)
        return _to_entity(model)
 
    def update(self, user_id: UUID, **fields) -> Optional[UserEntity]:
        model = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(model, key, value)
        self._db.flush()
        self._db.refresh(model)
        return _to_entity(model)
 
    def deactivate(self, user_id: UUID) -> bool:
        """Soft delete — solo marca is_active=False."""
        model = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        model.is_active = False
        self._db.flush()
        return True
 
    def assign_role(self, user_id: UUID, role_code: str) -> bool:
        role = self._db.query(RoleModel).filter(RoleModel.code == role_code).first()
        if not role:
            return False
 
        existing = self._db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).first()
        if existing:
            existing.role_id = role.id   # reemplaza rol actual
        else:
            self._db.add(UserRoleModel(user_id=user_id, role_id=role.id))
 
        self._db.flush()
        return True