from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid
from sqlalchemy import ForeignKey

class RolePermissionModel(Base):
    """Tabla pivot: qué permisos tiene cada rol."""
    __tablename__ = "role_permissions"
 
    role_id       = Column(UUID(as_uuid=True), ForeignKey("roles.id"),       primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
 
    # Relaciones
    role       = relationship("RoleModel",       back_populates="role_permissions")
    permission = relationship("PermissionModel", back_populates="role_permissions")
 