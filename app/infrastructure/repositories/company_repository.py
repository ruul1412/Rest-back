from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.company.company_entity import CompanyEntity
from app.infrastructure.models.company_model import CompanyModel
from app.domain.table.table_entity import TableEntity


def _to_entity(m: CompanyModel) -> CompanyEntity:
    return CompanyEntity(
        id=m.id,
        name=m.name,
        description=m.description,
        phone=m.phone,
        is_active=m.is_active,
        ruc=m.ruc
    )

class CompanyRepository:

    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        return self._db.query(CompanyModel.id).count()

    def get_all(self, skip: int = 0, limit: int | None = None) -> list[CompanyEntity]:
        q = self._db.query(CompanyModel).order_by(CompanyModel.name)
        if skip:
            q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return [_to_entity(m) for m in q.all()]

    def create(self, name: str, description: Optional[str], phone: Optional[str], ruc: Optional[str]) -> CompanyEntity: 
        m=CompanyModel(name=name, description=description, phone=phone,is_active=True, ruc=ruc)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, company_id: UUID, name: Optional[str], description: Optional[str], phone: Optional[str], is_active: bool, ruc: Optional[str]) -> Optional[CompanyEntity]:
        m = self._db.query(CompanyModel).filter(CompanyModel.id==company_id).first()
        if not m:
            return None
        m.name = name
        m.description = description
        m.phone = phone
        m.is_active = is_active
        m.ruc = ruc
        self._db.flush()
        return _to_entity(m)

    def delete(self, company_id: UUID) -> bool:
        m = self._db.query(CompanyModel).filter(CompanyModel.id==company_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True