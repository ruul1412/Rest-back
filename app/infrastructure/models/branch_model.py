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
    is_active = Column(Boolean, default=True) # ESTADO DE LA SUCURSAL (ACTIVA O INACTIVA)
    
    company = relationship("CompanyModel", back_populates="branches") # RELACION CON LA EMPRESA(company)
    branch_users = relationship("BranchUserModel", back_populates="branch") # RELACION CON LOS USUARIOS DE LA SUCURSAL
    branch_categories = relationship("CategoryModel", back_populates="branch") # RELACION CON LAS CATEGORIAS DE LA SUCURSAL
    branch_menu_day = relationship("MenuDayModel", back_populates="branch") # RELACION CON LOS DIAS DEL MENU DE LA SUCURSAL
    branch_order_groups = relationship("OrderGroupModel", back_populates="branch") # RELACION CON LOS GRUPOS DE ORDENES DE LA SUCURSAL
    branch_payments = relationship("PaymentModel", back_populates="branch") # RELACION CON LOS PAGOS DE LA SUCURSAL
    branch_products = relationship("ProductModel", back_populates="branch") # RELACION CON LOS PRODUCTOS DE LA SUCURSAL
    branch_product_types = relationship("ProductTypeModel", back_populates="branch") # RELACION CON LOS TIPOS DE PRODUCTOS DE LA SUCURSAL
    branch_tables = relationship("TableModel", back_populates="branch") # RELACION CON LAS MESAS DE LA SUCURSAL