from app.domain.enums.table_payment_enum import TableStatus
from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.infrastructure.db.mixins.auditable import AuditableBase
import uuid


class TableModel(Base, AuditableBase):
    __tablename__ = "tables"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number    = Column(Integer, nullable=False, unique=True)
    capacity  = Column(Integer, nullable=False)
    status    = Column(String(20), default=TableStatus.libre, nullable=False)
    description = Column(String(20), nullable=True)

    branch_id = Column( UUID(as_uuid=True),ForeignKey("branches.id"), primary_key=True)
    branch = relationship("BranchModel", back_populates="branch_tables")
    
    order_groups = relationship("OrderGroupModel", back_populates="table")

