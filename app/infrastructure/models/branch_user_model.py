
from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase


class BranchUserModel(Base, AuditableBase):
    __tablename__ = "branch_users"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"),primary_key=True)
    branch_id = Column( UUID(as_uuid=True),ForeignKey("branches.id"), primary_key=True)

    role_id = Column( UUID(as_uuid=True),ForeignKey("roles.id"), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    user = relationship("UserModel", back_populates="branch_users")
    branch = relationship("BranchModel", back_populates="branch_users")
    role = relationship("RoleModel", back_populates="branch_users")
