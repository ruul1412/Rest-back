from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password

from app.infrastructure.models.role_model import RoleModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.models.user_role_model import UserRoleModel


def seed_super_admin() -> None:
    email = (settings.SUPER_ADMIN_EMAIL or "").strip().lower()
    password = settings.SUPER_ADMIN_PASSWORD

    if not email or not password:
        raise RuntimeError(
            "Debes configurar SUPER_ADMIN_EMAIL y "
            "SUPER_ADMIN_PASSWORD en el archivo .env"
        )

    db = SessionLocal()

    try:
        # 1. Obtener o crear el rol global
        role = (
            db.query(RoleModel)
            .filter(RoleModel.code == "super_admin")
            .first()
        )

        if not role:
            role = RoleModel(
                name="Super Administrador",
                code="super_admin"
            )
            db.add(role)
            db.flush()

            print("Rol super_admin creado")

        # 2. Obtener o crear el usuario inicial
        user = (
            db.query(UserModel)
            .filter(UserModel.email == email)
            .first()
        )

        if not user:
            user = UserModel(
                email=email,
                password=hash_password(password),
                first_name=settings.SUPER_ADMIN_FIRST_NAME,
                last_name=settings.SUPER_ADMIN_LAST_NAME,
                is_active=True
            )

            db.add(user)
            db.flush()

            print("Usuario Super Admin creado")

        elif not user.is_active:
            raise RuntimeError(
                "La cuenta configurada para Super Admin está inactiva. "
                "Actívala antes de iniciar la aplicación."
            )

        # 3. Comprobar si ya tiene asignado super_admin
        assignment = (
            db.query(UserRoleModel)
            .filter(
                UserRoleModel.user_id == user.id,
                UserRoleModel.role_id == role.id
            )
            .first()
        )

        if not assignment:
            db.add(
                UserRoleModel(
                    user_id=user.id,
                    role_id=role.id
                )
            )
            print("Rol super_admin asignado")
            
        # El Super Admin no debe conservar otros roles globales
        db.query(UserRoleModel).filter(
            UserRoleModel.user_id == user.id,
            UserRoleModel.role_id != role.id
        ).delete(synchronize_session=False)

        db.commit()
        print("Seed Super Admin completado")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_super_admin()