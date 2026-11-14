from sqlalchemy import Column, String, Boolean, false, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid
from sqlalchemy.orm import relationship

class BranchModel(Base, AuditableBase):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(String,nullable=True) # REFERENTE AL NOMBRE GENERAL DE LA EMPRESA
    phone = Column(String,nullable=True)
    name = Column(String,nullable=False) # NOMBRE COMERCIAL
    address = Column(String,nullable=False) # DIRECCION DE LA SUCURSAL
    company_id = Column(UUID(as_uuid=True),ForeignKey("companys.id")) # ID DE LA EMPRESA A LA QUE PERTENECE
    company = relationship("CompanyModel", back_populates="branches") # RELACION CON LA EMPRESA(company)