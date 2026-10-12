from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from decimal import Decimal


@dataclass
class CategoryEntity:
    id:   UUID
    name: str


@dataclass
class ProductTypeEntity:
    id:           UUID
    name:         str
    code:         str
    has_variants: bool
    is_menu_item: bool
    deducts_stock: bool


@dataclass
class ProductVariantEntity:
    id:           UUID
    product_id:   UUID
    name:         str
    price:        Decimal
    orden_num:    int
    is_available: bool


@dataclass
class ProductEntity:
    id:           UUID
    name:         str
    sale_price:   Decimal
    is_available: bool
    is_active:    bool
    category_id:  Optional[UUID]     = None
    category_name: Optional[str]     = None
    type_id:      Optional[UUID]     = None
    type_code:    Optional[str]      = None
    type_name:    Optional[str]      = None
    cost_price:   Optional[Decimal]  = None
    image_url:    Optional[str]      = None
    stock:        Optional[int]      = None
    variants:     list[ProductVariantEntity] = field(default_factory=list)