from app.infrastructure.models.role_model import RoleModel


class RoleRepository:

    def __init__(self, db):
        self.db = db

    def get_by_name(self, name: str):
        return self.db.query(RoleModel).filter(RoleModel.name == name).first()

    def get_by_names(self, names: list[str]):
        return self.db.query(RoleModel).filter(RoleModel.name.in_(names)).all()