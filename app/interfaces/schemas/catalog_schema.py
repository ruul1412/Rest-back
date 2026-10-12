from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from decimal import Decimal


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreateRequest(BaseModel):
    name: str

class CategoryUpdateRequest(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id:   UUID
    name: str


# ── ProductType ───────────────────────────────────────────────────────────────

class ProductTypeResponse(BaseModel):
    id:            UUID
    name:          str
    code:          str
    has_variants:  bool
    is_menu_item:  bool
    deducts_stock: bool


# ── ProductVariant ────────────────────────────────────────────────────────────

class VariantCreateRequest(BaseModel):
    name:      str
    price:     Decimal
    orden_num: int = 1

class VariantUpdateRequest(BaseModel):
    name:         Optional[str]     = None
    price:        Optional[Decimal] = None
    orden_num:    Optional[int]     = None
    is_available: Optional[bool]    = None

class VariantResponse(BaseModel):
    id:           UUID
    name:         str
    price:        Decimal
    orden_num:    int
    is_available: bool


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreateRequest(BaseModel):
    name:         str
    sale_price:   Decimal
    category_id:  UUID
    type_id:      Optional[UUID]    = None
    cost_price:   Optional[Decimal] = None
    image_url:    Optional[str]     = None
    stock:        Optional[int]     = None

    @field_validator("sale_price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return v


class ProductUpdateRequest(BaseModel):
    name:         Optional[str]     = None
    sale_price:   Optional[Decimal] = None
    cost_price:   Optional[Decimal] = None
    category_id:  Optional[UUID]    = None
    type_id:      Optional[UUID]    = None
    image_url:    Optional[str]     = None
    stock:        Optional[int]     = None
    is_available: Optional[bool]    = None


class ProductResponse(BaseModel):
    id:            UUID
    name:          str
    sale_price:    Decimal
    cost_price:    Optional[Decimal] = None
    image_url:     Optional[str]     = None
    stock:         Optional[int]     = None
    is_available:  bool
    is_active:     bool
    category_id:   Optional[UUID]    = None
    category_name: Optional[str]     = None
    type_id:       Optional[UUID]    = None
    type_code:     Optional[str]     = None
    type_name:     Optional[str]     = None
    variants:      list[VariantResponse] = []