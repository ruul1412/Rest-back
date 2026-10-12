from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr


class AuditableBase:

    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    # @declared_attr
    # def deleted_at(cls):
    #     return Column(DateTime(timezone=True), nullable=True)

    # # 🔥 TRAZABILIDAD (MUY IMPORTANTE)
    # @declared_attr
    # def created_by(cls):
    #     return Column(String, nullable=True)

    # @declared_attr
    # def updated_by(cls):
    #     return Column(String, nullable=True)