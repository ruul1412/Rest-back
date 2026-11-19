"""
Seed: roles + permisos + asignación rol→permiso.
Se ejecuta en cada startup — es idempotente (no duplica nada).
"""

from app.core.database import SessionLocal
from app.infrastructure.models.role_model import RoleModel
from app.infrastructure.models.permission_model import PermissionModel
from app.infrastructure.models.role_permission_model import RolePermissionModel


# ── 1. Permisos del sistema ───────────────────────────────────────────────────

PERMISSIONS = [
    # Usuarios
    ("users.create",           "Crear usuarios"),
    ("users.read",             "Ver usuarios"),
    ("users.update",           "Editar usuarios"),
    ("users.delete",           "Desactivar usuarios"),
    ("users.assign_roles",     "Asignar roles a usuarios"),
    # Categorías
    ("categories.create",      "Crear categorías"),
    ("categories.read",        "Ver categorías"),
    ("categories.update",      "Editar categorías"),
    ("categories.delete",      "Eliminar categorías"),
    # Productos
    ("products.create",        "Crear productos"),
    ("products.read",          "Ver productos"),
    ("products.update",        "Editar productos"),
    ("products.delete",        "Eliminar productos"),
    # Menú del día
    ("menu.configure",         "Configurar menú del día"),
    ("menu.read",              "Ver menú del día"),
    # Mesas
    ("tables.manage",          "Crear/editar mesas"),
    ("tables.read",            "Ver mesas"),
    ("tables.update_status",   "Cambiar estado de mesa"),
    # Órdenes
    ("orders.create",          "Crear órdenes"),
    ("orders.read",            "Ver órdenes"),
    ("orders.update",          "Editar órdenes"),
    ("orders.cancel",          "Cancelar órdenes"),
    # Pagos
    ("payments.process",       "Procesar pagos"),
    ("payments.read",          "Ver pagos"),
    # Reportes
    ("reports.read",           "Ver reportes"),
    # permisos 
    ("permissions.read",   "Ver permisos del sistema"),
    ("permissions.assign", "Asignar/revocar permisos a usuarios"), 
]


# ── 2. Permisos por rol ───────────────────────────────────────────────────────

ALL = [p[0] for p in PERMISSIONS]

ROLE_PERMISSIONS = {
    "admin": ALL,
    "mesero": [
        "products.read",
        "categories.read",
        "menu.read",
        "tables.read",
        "tables.update_status",
        "orders.create",
        "orders.read",
        "orders.update",
    ],
    "cajero": [
        "products.read",
        "categories.read",
        "menu.read",
        "tables.read",
        "orders.read",
        "payments.process",
        "payments.read",
        "reports.read",
    ],
    "cocina": [
        "menu.configure",
        "menu.read",
        "orders.read",
        "orders.update",
    ],
    "bartender": [
        "products.read",
        "categories.read",
        "menu.read",
        "orders.create",
        "orders.read",
        "orders.update",
    ],
}


# ── 3. Roles ──────────────────────────────────────────────────────────────────

ROLES = [
    {"name": "Administrador", "code": "admin"},
    {"name": "Mesero",        "code": "mesero"},
    {"name": "Cocina",        "code": "cocina"},
    {"name": "Bartender",     "code": "bartender"},
    {"name": "Cajero",        "code": "cajero"},
]


# ── 4. Seed ───────────────────────────────────────────────────────────────────

def seed_roles() -> None:
    db = SessionLocal()
    try:
        # ── Permisos ──────────────────────────────────────────────────────────
        perm_map: dict[str, PermissionModel] = {}
        for code, description in PERMISSIONS:
            perm = db.query(PermissionModel).filter_by(code=code).first()
            if not perm:
                perm = PermissionModel(code=code, description=description)
                db.add(perm)
                db.flush()
                print(f"  ✅ Permiso: {code}")
            perm_map[code] = perm

        # ── Roles ─────────────────────────────────────────────────────────────
        role_map: dict[str, RoleModel] = {}
        for r in ROLES:
            role = db.query(RoleModel).filter_by(code=r["code"]).first()
            if not role:
                role = RoleModel(name=r["name"], code=r["code"])
                db.add(role)
                db.flush()
                print(f"  ✅ Rol: {r['code']}")
            role_map[r["code"]] = role

        # ── Asignaciones rol → permiso ────────────────────────────────────────
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = role_map.get(role_code)
            if not role:
                continue
            for perm_code in perm_codes:
                perm = perm_map.get(perm_code)
                if not perm:
                    continue
                exists = db.query(RolePermissionModel).filter_by(
                    role_id=role.id, permission_id=perm.id
                ).first()
                if not exists:
                    db.add(RolePermissionModel(role_id=role.id, permission_id=perm.id))

        db.commit()
        print("🚀 seed_roles completado")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed_roles: {e}")
        raise
    finally:
        db.close()