from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class UserModel(Base, AuditableBase):
    __tablename__ = "users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email      = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)

    first_name = Column(String, nullable=True)
    last_name  = Column(String, nullable=True)
    phone      = Column(String, nullable=True)
    dni        = Column(String, nullable=True)
    is_active  = Column(Boolean, default=True)

    user_roles   = relationship("UserRoleModel",   back_populates="user", uselist=False)
    order_groups = relationship("OrderGroupModel", back_populates="user")

    user_permissions = relationship("UserPermissionModel", back_populates="user",
                                    foreign_keys="UserPermissionModel.user_id")