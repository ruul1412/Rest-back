from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid

class CompanyModel(Base, AuditableBase):
    __tablename__ = "companys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(String,nullable=True) # REFERENTE AL NOMBRE GENERAL DE LA EMPRESA
    phone = Column(String,nullable=True)
    is_active= Column(Boolean,default=True)
    name = Column(String,nullable=False) # NOMBRE COMERCIAL
    ruc = Column(String,nullable=True)
    branches = relationship("BranchModel", back_populates="company") # RELACION CON LAS SUCURSALES
    