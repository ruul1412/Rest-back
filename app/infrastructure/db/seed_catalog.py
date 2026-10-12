"""
Seed: tipos de producto y categorías base.
Idempotente — no duplica si ya existen.
"""

from app.core.database import SessionLocal
from app.infrastructure.models.product_type_model import ProductTypeModel
from app.infrastructure.models.category_model import CategoryModel


PRODUCT_TYPES = [
    {"name": "Plato menú",  "code": "plato_menu",  "has_variants": False, "is_menu_item": True,  "deducts_stock": True},
    {"name": "Carta",       "code": "carta",        "has_variants": False, "is_menu_item": False, "deducts_stock": False},
    {"name": "Entrada",     "code": "entrada",      "has_variants": False, "is_menu_item": False, "deducts_stock": False},
    {"name": "Bebida",      "code": "bebida",       "has_variants": True,  "is_menu_item": False, "deducts_stock": True},
    {"name": "Postre",      "code": "postre",       "has_variants": False, "is_menu_item": False, "deducts_stock": False},
    {"name": "Adicional",   "code": "adicional",    "has_variants": False, "is_menu_item": False, "deducts_stock": False},
    {"name": "Extra",   "code": "extra",    "has_variants": False, "is_menu_item": False, "deducts_stock": False},
]

CATEGORIES = [
    "Menú del día",
    "Carta",
    "Entradas",
    "Bebidas",
    "Postres",
    "Adicionales",
    "Extras",
]


def seed_catalog() -> None:
    db = SessionLocal()
    try:
        for pt in PRODUCT_TYPES:
            exists = db.query(ProductTypeModel).filter_by(code=pt["code"]).first()
            if not exists:
                db.add(ProductTypeModel(**pt))
                print(f"  ✅ ProductType: {pt['code']}")

        for name in CATEGORIES:
            exists = db.query(CategoryModel).filter_by(name=name).first()
            if not exists:
                db.add(CategoryModel(name=name))
                print(f"  ✅ Categoría: {name}")

        db.commit()
        print("🚀 seed_catalog completado")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed_catalog: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_catalog()