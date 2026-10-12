"""
Script de seed: crea rol 'admin' y usuario de prueba.

Uso:
    python -m app.infrastructure.db.seed_admin
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.infrastructure.models.role_model import RoleModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.models.user_role_model import UserRoleModel


def seed_admin() -> None:
    db = SessionLocal()
    try:
        # ── Rol admin ─────────────────────────────────────────────────────────
        role = db.query(RoleModel).filter_by(code="admin").first()
        if not role:
            role = RoleModel(name="Administrador", code="admin")
            db.add(role)
            db.flush()   # obtiene el id sin commitear aún
            print("✅ Rol 'admin' creado")
        else:
            print("ℹ️  Rol 'admin' ya existe")

        # ── Usuario admin ─────────────────────────────────────────────────────
        user = db.query(UserModel).filter_by(email="raulpisc@gmail.com").first()
        if not user:
            user = UserModel(
                email="raulpisc@gmail.com",
                password=hash_password("201411"),
                first_name="Admin",
                last_name="Restaurant",
                is_active=True,
            )
            db.add(user)
            db.flush()
            print("✅ Usuario 'admin@restaurant.com' creado")
        else:
            print("ℹ️  Usuario ya existe")

        # ── Asignar rol ───────────────────────────────────────────────────────
        existing = db.query(UserRoleModel).filter_by(user_id=user.id).first()
        if not existing:
            db.add(UserRoleModel(user_id=user.id, role_id=role.id))
            print("✅ Rol asignado al usuario")
        else:
            print("ℹ️  Usuario ya tiene rol asignado")

        db.commit()
        print("\n🚀 Seed completado")
        print("   Email:    raulpisc@gmail.com")
        print("   Password: 201411")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()