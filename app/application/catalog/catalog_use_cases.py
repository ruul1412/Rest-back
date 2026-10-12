from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.catalog_schema import (
    CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse,
    ProductCreateRequest, ProductUpdateRequest, ProductResponse,
    ProductTypeResponse, VariantCreateRequest, VariantUpdateRequest, VariantResponse,
)
from app.infrastructure.repositories.catalog_repository import (
    CategoryRepository, ProductRepository, ProductTypeRepository,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cat_resp(e) -> CategoryResponse:
    return CategoryResponse(id=e.id, name=e.name)

def _type_resp(e) -> ProductTypeResponse:
    return ProductTypeResponse(
        id=e.id, name=e.name, code=e.code,
        has_variants=e.has_variants,
        is_menu_item=e.is_menu_item,
        deducts_stock=e.deducts_stock,
    )

def _prod_resp(e) -> ProductResponse:
    return ProductResponse(
        id=e.id, name=e.name,
        sale_price=e.sale_price, cost_price=e.cost_price,
        image_url=e.image_url, stock=e.stock,
        is_available=e.is_available, is_active=e.is_active,
        category_id=e.category_id, category_name=e.category_name,
        type_id=e.type_id, type_code=e.type_code, type_name=e.type_name,
        variants=[
            VariantResponse(
                id=v.id, name=v.name, price=v.price,
                orden_num=v.orden_num, is_available=v.is_available,
            ) for v in e.variants
        ],
    )


# ── Category Use Cases ────────────────────────────────────────────────────────

class ListCategoriesUseCase:
    def __init__(self, repo: CategoryRepository): self._repo = repo
    def execute(self) -> list[CategoryResponse]:
        return [_cat_resp(e) for e in self._repo.get_all()]


class CreateCategoryUseCase:
    def __init__(self, repo: CategoryRepository): self._repo = repo
    def execute(self, data: CategoryCreateRequest) -> CategoryResponse:
        if self._repo.name_exists(data.name):
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
        return _cat_resp(self._repo.create(data.name))


class UpdateCategoryUseCase:
    def __init__(self, repo: CategoryRepository): self._repo = repo
    def execute(self, category_id: UUID, data: CategoryUpdateRequest) -> CategoryResponse:
        entity = self._repo.update(category_id, data.name)
        if not entity:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        return _cat_resp(entity)


class DeleteCategoryUseCase:
    def __init__(self, repo: CategoryRepository): self._repo = repo
    def execute(self, category_id: UUID) -> dict:
        if self._repo.has_products(category_id):
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar: la categoría tiene productos activos",
            )
        if not self._repo.delete(category_id):
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        return {"detail": "Categoría eliminada"}


# ── ProductType Use Cases ─────────────────────────────────────────────────────

class ListProductTypesUseCase:
    def __init__(self, repo: ProductTypeRepository): self._repo = repo
    def execute(self) -> list[ProductTypeResponse]:
        return [_type_resp(e) for e in self._repo.get_all()]


# ── Product Use Cases ─────────────────────────────────────────────────────────

class ListProductsUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, category_id: UUID = None) -> list[ProductResponse]:
        if category_id:
            return [_prod_resp(e) for e in self._repo.get_by_category(category_id)]
        return [_prod_resp(e) for e in self._repo.get_all()]


class GetProductUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, product_id: UUID) -> ProductResponse:
        entity = self._repo.get_by_id(product_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return _prod_resp(entity)


class CreateProductUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, data: ProductCreateRequest) -> ProductResponse:
        entity = self._repo.create(
            name=data.name,
            sale_price=data.sale_price,
            cost_price=data.cost_price,
            category_id=data.category_id,
            type_id=data.type_id,
            image_url=data.image_url,
            stock=data.stock,
        )
        return _prod_resp(entity)


class UpdateProductUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, product_id: UUID, data: ProductUpdateRequest) -> ProductResponse:
        entity = self._repo.update(
            product_id,
            name=data.name,
            sale_price=data.sale_price,
            cost_price=data.cost_price,
            category_id=data.category_id,
            type_id=data.type_id,
            image_url=data.image_url,
            stock=data.stock,
            is_available=data.is_available,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return _prod_resp(entity)


class DeactivateProductUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, product_id: UUID) -> dict:
        if not self._repo.deactivate(product_id):
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return {"detail": "Producto desactivado"}


# ── Variant Use Cases ─────────────────────────────────────────────────────────

class AddVariantUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, product_id: UUID, data: VariantCreateRequest) -> VariantResponse:
        product = self._repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if not product.type_code == "bebida":
            raise HTTPException(
                status_code=400,
                detail="Solo los productos de tipo 'bebida' pueden tener variantes",
            )
        entity = self._repo.add_variant(
            product_id=product_id,
            name=data.name, price=data.price, orden_num=data.orden_num,
        )
        return VariantResponse(
            id=entity.id, name=entity.name, price=entity.price,
            orden_num=entity.orden_num, is_available=entity.is_available,
        )


class UpdateVariantUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, variant_id: UUID, data: VariantUpdateRequest) -> VariantResponse:
        entity = self._repo.update_variant(
            variant_id,
            name=data.name, price=data.price,
            orden_num=data.orden_num, is_available=data.is_available,
        )
        if not entity:
            raise HTTPException(status_code=404, detail="Variante no encontrada")
        return VariantResponse(
            id=entity.id, name=entity.name, price=entity.price,
            orden_num=entity.orden_num, is_available=entity.is_available,
        )


class DeleteVariantUseCase:
    def __init__(self, repo: ProductRepository): self._repo = repo
    def execute(self, variant_id: UUID) -> dict:
        if not self._repo.delete_variant(variant_id):
            raise HTTPException(status_code=404, detail="Variante no encontrada")
        return {"detail": "Variante eliminada"}