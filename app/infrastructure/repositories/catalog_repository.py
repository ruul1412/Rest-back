from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.infrastructure.models.category_model import CategoryModel
from app.infrastructure.models.product_model import ProductModel
from app.infrastructure.models.product_type_model import ProductTypeModel
from app.infrastructure.models.product_varient_model import ProductVariantModel
from app.domain.catalog.catalog_entity import (
    CategoryEntity, ProductEntity, ProductTypeEntity, ProductVariantEntity
)


# ── Mappers ───────────────────────────────────────────────────────────────────

def _category_to_entity(m: CategoryModel) -> CategoryEntity:
    return CategoryEntity(id=m.id, name=m.name)


def _type_to_entity(m: ProductTypeModel) -> ProductTypeEntity:
    return ProductTypeEntity(
        id=m.id, name=m.name, code=m.code,
        has_variants=m.has_variants,
        is_menu_item=m.is_menu_item,
        deducts_stock=m.deducts_stock,
    )


def _variant_to_entity(m: ProductVariantModel) -> ProductVariantEntity:
    return ProductVariantEntity(
        id=m.id, product_id=m.product_id,
        name=m.name, price=m.price,
        orden_num=m.orden_num, is_available=m.is_available,
    )


def _product_to_entity(m: ProductModel) -> ProductEntity:
    return ProductEntity(
        id=m.id,
        name=m.name,
        sale_price=m.sale_price,
        cost_price=m.cost_price,
        image_url=m.image_url,
        stock=m.stock,
        is_available=m.is_available,
        is_active=m.is_active,
        category_id=m.category_id,
        category_name=m.category.name if m.category else None,
        type_id=m.type_id,
        type_code=m.product_type.code if m.product_type else None,
        type_name=m.product_type.name if m.product_type else None,
        variants=[_variant_to_entity(v) for v in (m.variants or [])],
    )


# ── Category Repository ───────────────────────────────────────────────────────

class CategoryRepository:

    def __init__(self, db: Session):
        self._db = db

    def get_all(self) -> list[CategoryEntity]:
        return [_category_to_entity(m) for m in
                self._db.query(CategoryModel).order_by(CategoryModel.name).all()]

    def get_by_id(self, category_id: UUID) -> Optional[CategoryEntity]:
        m = self._db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        return _category_to_entity(m) if m else None

    def name_exists(self, name: str) -> bool:
        return self._db.query(CategoryModel.id).filter(
            CategoryModel.name == name).first() is not None

    def create(self, name: str) -> CategoryEntity:
        m = CategoryModel(name=name)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _category_to_entity(m)

    def update(self, category_id: UUID, name: str) -> Optional[CategoryEntity]:
        m = self._db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        if not m:
            return None
        m.name = name
        self._db.flush()
        return _category_to_entity(m)

    def delete(self, category_id: UUID) -> bool:
        m = self._db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True

    def has_products(self, category_id: UUID) -> bool:
        return self._db.query(ProductModel.id).filter(
            ProductModel.category_id == category_id,
            ProductModel.is_active == True,
        ).first() is not None


# ── ProductType Repository ────────────────────────────────────────────────────

class ProductTypeRepository:

    def __init__(self, db: Session):
        self._db = db

    def get_all(self) -> list[ProductTypeEntity]:
        return [_type_to_entity(m) for m in
                self._db.query(ProductTypeModel).order_by(ProductTypeModel.name).all()]

    def get_by_id(self, type_id: UUID) -> Optional[ProductTypeEntity]:
        m = self._db.query(ProductTypeModel).filter(ProductTypeModel.id == type_id).first()
        return _type_to_entity(m) if m else None


# ── Product Repository ────────────────────────────────────────────────────────

class ProductRepository:

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self):
        return (
            self._db.query(ProductModel)
            .options(
                joinedload(ProductModel.category),
                joinedload(ProductModel.product_type),
                joinedload(ProductModel.variants),
            )
        )

    def get_all(self, only_active: bool = True) -> list[ProductEntity]:
        q = self._base_query()
        if only_active:
            q = q.filter(ProductModel.is_active == True)
        return [_product_to_entity(m) for m in q.order_by(ProductModel.name).all()]

    def get_by_id(self, product_id: UUID) -> Optional[ProductEntity]:
        m = self._base_query().filter(ProductModel.id == product_id).first()
        return _product_to_entity(m) if m else None

    def get_by_category(self, category_id: UUID) -> list[ProductEntity]:
        return [_product_to_entity(m) for m in
                self._base_query()
                .filter(ProductModel.category_id == category_id,
                        ProductModel.is_active == True)
                .order_by(ProductModel.name).all()]

    def create(self, **kwargs) -> ProductEntity:
        m = ProductModel(**kwargs)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        # Reload con relationships
        return _product_to_entity(
            self._base_query().filter(ProductModel.id == m.id).first()
        )

    def update(self, product_id: UUID, **fields) -> Optional[ProductEntity]:
        m = self._db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        self._db.flush()
        return _product_to_entity(
            self._base_query().filter(ProductModel.id == product_id).first()
        )

    def deactivate(self, product_id: UUID) -> bool:
        m = self._db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not m:
            return False
        m.is_active = False
        self._db.flush()
        return True

    # ── Variantes ─────────────────────────────────────────────────────────────

    def add_variant(self, product_id: UUID, name: str, price, orden_num: int) -> Optional[ProductVariantEntity]:
        m = ProductVariantModel(
            product_id=product_id, name=name,
            price=price, orden_num=orden_num,
        )
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _variant_to_entity(m)

    def update_variant(self, variant_id: UUID, **fields) -> Optional[ProductVariantEntity]:
        m = self._db.query(ProductVariantModel).filter(
            ProductVariantModel.id == variant_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        self._db.flush()
        return _variant_to_entity(m)

    def delete_variant(self, variant_id: UUID) -> bool:
        m = self._db.query(ProductVariantModel).filter(
            ProductVariantModel.id == variant_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True