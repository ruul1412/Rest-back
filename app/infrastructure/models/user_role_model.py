from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.core.database import Base

class UserRoleModel(Base):
    __tablename__ = "user_roles"
 
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
 
    user = relationship("UserModel",  back_populates="user_roles")
    role = relationship("RoleModel",  back_populates="user_roles")
