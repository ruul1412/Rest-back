from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.interfaces.schemas.catalog_schema import (
    CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse,
    ProductCreateRequest, ProductUpdateRequest, ProductResponse,
    ProductTypeResponse, VariantCreateRequest, VariantUpdateRequest, VariantResponse,
)
from app.application.catalog.catalog_use_cases import (
    ListCategoriesUseCase, CreateCategoryUseCase,
    UpdateCategoryUseCase, DeleteCategoryUseCase,
    ListProductTypesUseCase,
    ListProductsUseCase, GetProductUseCase, CreateProductUseCase,
    UpdateProductUseCase, DeactivateProductUseCase,
    AddVariantUseCase, UpdateVariantUseCase, DeleteVariantUseCase,
)
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.infrastructure.repositories.catalog_repository import (
    CategoryRepository, ProductRepository, ProductTypeRepository,
)

# ── Routers ───────────────────────────────────────────────────────────────────


category_router = APIRouter(prefix="/categories", tags=["Categories"])
product_type_router = APIRouter(prefix="/product-types", tags=["Product Types"])
product_router = APIRouter(prefix="/products", tags=["Products"])

_admin        = Depends(require_roles(["admin"]))
_admin_cocina = Depends(require_roles(["admin", "cocina"]))
_all_staff    = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))


# ── Categories ────────────────────────────────────────────────────────────────

@category_router.get("", response_model=list[CategoryResponse], dependencies=[_all_staff])
def list_categories(db: Session = Depends(get_db)):
    return ListCategoriesUseCase(CategoryRepository(db)).execute()


@category_router.post("", response_model=CategoryResponse, status_code=201, dependencies=[_admin])
def create_category(data: CategoryCreateRequest, db: Session = Depends(get_db)):
    result = CreateCategoryUseCase(CategoryRepository(db)).execute(data)
    db.commit()
    return result


@category_router.put("/{category_id}", response_model=CategoryResponse, dependencies=[_admin])
def update_category(category_id: UUID, data: CategoryUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateCategoryUseCase(CategoryRepository(db)).execute(category_id, data)
    db.commit()
    return result


@category_router.delete("/{category_id}", dependencies=[_admin])
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    result = DeleteCategoryUseCase(CategoryRepository(db)).execute(category_id)
    db.commit()
    return result


# ── Product Types ─────────────────────────────────────────────────────────────

@product_type_router.get("", response_model=list[ProductTypeResponse], dependencies=[_all_staff])
def list_product_types(db: Session = Depends(get_db)):
    return ListProductTypesUseCase(ProductTypeRepository(db)).execute()


# ── Products ──────────────────────────────────────────────────────────────────

@product_router.get("", response_model=list[ProductResponse], dependencies=[_all_staff])
def list_products(category_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    return ListProductsUseCase(ProductRepository(db)).execute(category_id)


@product_router.get("/{product_id}", response_model=ProductResponse, dependencies=[_all_staff])
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    return GetProductUseCase(ProductRepository(db)).execute(product_id)


@product_router.post("", response_model=ProductResponse, status_code=201, dependencies=[_admin])
def create_product(data: ProductCreateRequest, db: Session = Depends(get_db)):
    result = CreateProductUseCase(ProductRepository(db)).execute(data)
    db.commit()
    return result


@product_router.put("/{product_id}", response_model=ProductResponse, dependencies=[_admin])
def update_product(product_id: UUID, data: ProductUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateProductUseCase(ProductRepository(db)).execute(product_id, data)
    db.commit()
    return result


@product_router.delete("/{product_id}", dependencies=[_admin])
def deactivate_product(product_id: UUID, db: Session = Depends(get_db)):
    result = DeactivateProductUseCase(ProductRepository(db)).execute(product_id)
    db.commit()
    return result


# ── Variants (solo bebidas) ───────────────────────────────────────────────────

@product_router.post("/{product_id}/variants", response_model=VariantResponse, status_code=201, dependencies=[_admin])
def add_variant(product_id: UUID, data: VariantCreateRequest, db: Session = Depends(get_db)):
    result = AddVariantUseCase(ProductRepository(db)).execute(product_id, data)
    db.commit()
    return result


@product_router.put("/variants/{variant_id}", response_model=VariantResponse, dependencies=[_admin])
def update_variant(variant_id: UUID, data: VariantUpdateRequest, db: Session = Depends(get_db)):
    result = UpdateVariantUseCase(ProductRepository(db)).execute(variant_id, data)
    db.commit()
    return result


@product_router.delete("/variants/{variant_id}", dependencies=[_admin])
def delete_variant(variant_id: UUID, db: Session = Depends(get_db)):
    result = DeleteVariantUseCase(ProductRepository(db)).execute(variant_id)
    db.commit()
    return result