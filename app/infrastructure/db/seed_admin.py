from app.infrastructure.db.seed_super_admin import seed_super_admin


def seed_admin() -> None:
    seed_super_admin()


if __name__ == "__main__":
    seed_super_admin()