from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

class PermissionModel(Base, AuditableBase):
    __tablename__ = "permissions"
 
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code        = Column(String, nullable=False, unique=True)   # clave única, ej: 'menu.configure'
    description = Column(String, nullable=True)
 
    # Relaciones
    role_permissions = relationship("RolePermissionModel", back_populates="permission")
    user_permissions = relationship("UserPermissionModel", back_populates="permission")