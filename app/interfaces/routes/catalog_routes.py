from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.infrastructure.unit_of_work import UnitOfWork

# ── Routers ───────────────────────────────────────────────────────────────────


category_router = APIRouter(prefix="/categories", tags=["Categories"])
product_type_router = APIRouter(prefix="/product-types", tags=["Product Types"])
product_router = APIRouter(prefix="/products", tags=["Products"])


def route_message(message: str):
    def decorator(func):
        func.response_message = message
        return func
    return decorator


_admin        = Depends(require_roles(["admin"]))
_admin_cocina = Depends(require_roles(["admin", "cocina"]))
_all_staff    = Depends(require_roles(["admin", "mesero", "cajero", "cocina", "bartender"]))


# ── Categories ────────────────────────────────────────────────────────────────

@route_message("Categorías obtenidas correctamente")
@category_router.get("", dependencies=[_all_staff])
def list_categories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return ListCategoriesUseCase(CategoryRepository(db)).execute(page=page, page_size=page_size)


@route_message("Categoría creada correctamente")
@category_router.post("", response_model=CategoryResponse, status_code=201, dependencies=[_admin])
def create_category(data: CategoryCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateCategoryUseCase(uow.categories).execute(data)
    uow.commit()
    return result


@route_message("Categoría actualizada correctamente")
@category_router.put("/{category_id}", response_model=CategoryResponse, dependencies=[_admin])
def update_category(category_id: UUID, data: CategoryUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateCategoryUseCase(uow.categories).execute(category_id, data)
    uow.commit()
    return result


@route_message("Categoría eliminada correctamente")
@category_router.delete("/{category_id}", dependencies=[_admin])
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteCategoryUseCase(uow.categories).execute(category_id)
    uow.commit()
    return result


# ── Product Types ─────────────────────────────────────────────────────────────

@route_message("Tipos de producto obtenidos correctamente")
@product_type_router.get("", dependencies=[_all_staff])
def list_product_types(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return ListProductTypesUseCase(ProductTypeRepository(db)).execute(page=page, page_size=page_size)


# ── Products ──────────────────────────────────────────────────────────────────

@route_message("Productos obtenidos correctamente")
@product_router.get("", dependencies=[_all_staff])
def list_products(
    category_id: Optional[UUID] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return ListProductsUseCase(ProductRepository(db)).execute(category_id=category_id, page=page, page_size=page_size)


@route_message("Producto obtenido correctamente")
@product_router.get("/{product_id}", response_model=ProductResponse, dependencies=[_all_staff])
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    return GetProductUseCase(ProductRepository(db)).execute(product_id)


@route_message("Producto creado correctamente")
@product_router.post("", response_model=ProductResponse, status_code=201, dependencies=[_admin])
def create_product(data: ProductCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = CreateProductUseCase(uow.products).execute(data)
    uow.commit()
    return result


@route_message("Producto actualizado correctamente")
@product_router.put("/{product_id}", response_model=ProductResponse, dependencies=[_admin])
def update_product(product_id: UUID, data: ProductUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateProductUseCase(uow.products).execute(product_id, data)
    uow.commit()
    return result


@route_message("Producto desactivado correctamente")
@product_router.delete("/{product_id}", dependencies=[_admin])
def deactivate_product(product_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeactivateProductUseCase(uow.products).execute(product_id)
    uow.commit()
    return result


# ── Variants (solo bebidas) ───────────────────────────────────────────────────

@route_message("Variante agregada correctamente")
@product_router.post("/{product_id}/variants", response_model=VariantResponse, status_code=201, dependencies=[_admin])
def add_variant(product_id: UUID, data: VariantCreateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = AddVariantUseCase(uow.products).execute(product_id, data)
    uow.commit()
    return result


@route_message("Variante actualizada correctamente")
@product_router.put("/variants/{variant_id}", response_model=VariantResponse, dependencies=[_admin])
def update_variant(variant_id: UUID, data: VariantUpdateRequest, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = UpdateVariantUseCase(uow.products).execute(variant_id, data)
    uow.commit()
    return result


@route_message("Variante eliminada correctamente")
@product_router.delete("/variants/{variant_id}", dependencies=[_admin])
def delete_variant(variant_id: UUID, db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    result = DeleteVariantUseCase(uow.products).execute(variant_id)
    uow.commit()
    return result