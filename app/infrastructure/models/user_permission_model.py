import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase


class UserPermissionModel(Base, AuditableBase):
    
    __tablename__ = "user_permissions"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"),       primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)

    granted_by  = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # quién otorgó el permiso → trazabilidad obligatoria

    expires_at  = Column(DateTime(timezone=True), nullable=True)
    # NULL  = permanente
    # fecha = se revoca automáticamente al vencer

    reason      = Column(String, nullable=True)
    # "Ausencia de admin del 15 al 20 de junio"

    # Relaciones
    user       = relationship("UserModel",       foreign_keys=[user_id],   back_populates="user_permissions")
    permission = relationship("PermissionModel", back_populates="user_permissions")
    granted_by_user = relationship("UserModel",  foreign_keys=[granted_by])