from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.repositories.catalog_repository import CategoryRepository, ProductRepository, ProductTypeRepository
from app.infrastructure.repositories.menu_repository import MenuRepository
from app.infrastructure.repositories.order_repository import OrderGroupRepository, OrderRepository
from app.infrastructure.repositories.payment_repository import PaymentRepository
from app.infrastructure.repositories.permission_repository import PermissionRepository
from app.infrastructure.repositories.table_repository import TableRepository
from app.infrastructure.repositories.user_repository import UserRepository


class UnitOfWork:
    """Coordina varios repos sobre la misma sesión SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.permissions = PermissionRepository(db)
        self.categories = CategoryRepository(db)
        self.products = ProductRepository(db)
        self.product_types = ProductTypeRepository(db)
        self.tables = TableRepository(db)
        self.menu = MenuRepository(db)
        self.orders = OrderRepository(db)
        self.order_groups = OrderGroupRepository(db)
        self.payments = PaymentRepository(db)

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False
