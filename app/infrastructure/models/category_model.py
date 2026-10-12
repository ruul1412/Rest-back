from sqlalchemy import Column, String
from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.db.mixins.auditable import AuditableBase
from sqlalchemy.orm import relationship

class CategoryModel(Base, AuditableBase):
    __tablename__ = "categories"
 
    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
 
    products = relationship("ProductModel", back_populates="category")
