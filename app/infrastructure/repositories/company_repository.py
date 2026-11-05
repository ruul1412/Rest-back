from sqlalchemy.orm import Session
from app.infrastructure.models.company_model import CompanyModel


class CompanyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, description: str, phone: str, is_active: bool, name: str, ruc: str):
        company = CompanyModel(
            description=description,
            phone=phone,
            is_active=is_active,
            name=name,
            ruc=ruc
        )
        self.db.add(company)
        self.db.flush()
        self.db.refresh(company)
        return company 

    # COMPLETAR EL DELETE Y UPDATE

    def get_all(self):
        return self.db.query(CompanyModel).filter(
            CompanyModel.is_active == True
            # ProductModel.is_deleted == False
        ).all()

    def ruc_exists(self, ruc: str):
        return self.db.query(CompanyModel).filter(
            CompanyModel.ruc == ruc
        ).first()