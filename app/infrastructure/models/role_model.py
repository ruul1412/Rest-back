from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid
 
class RoleModel(Base, AuditableBase):
    __tablename__ = "roles"
 
    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False) 
    
    user_roles = relationship("UserRoleModel", back_populates="role")
    role_permissions = relationship("RolePermissionModel", back_populates="role")
    