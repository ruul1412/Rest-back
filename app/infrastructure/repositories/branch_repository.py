from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.branch.branch_entity import BranchEntity
from app.infrastructure.models.branch_model import BranchModel
from app.domain.table.table_entity import TableEntity


def _to_entity(m: BranchModel) -> BranchEntity:
    return BranchEntity(
        id=m.id,
        name=m.name,
        description=m.description,
        phone=m.phone,
        address=m.address
    )

class BranchRepository:

    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        return self._db.query(BranchModel.id).count()

    def get_all(self, skip: int = 0, limit: int | None = None) -> list[BranchEntity]:
        q = self._db.query(BranchModel).order_by(BranchModel.name)
        if skip:
            q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return [_to_entity(m) for m in q.all()]

    def create(self, name: str, description: Optional[str], phone: Optional[str], address: str, company_id: UUID) -> BranchEntity: 
        m=BranchModel(name=name, description=description, phone=phone,address=address, company_id=company_id)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, branch_id: UUID, name: Optional[str], description: Optional[str], phone: Optional[str], address: str) -> Optional[BranchEntity]:
        m = self._db.query(BranchModel).filter(BranchModel.id==branch_id).first()
        if not m:
            return None
        m.name = name
        m.description = description
        m.phone = phone
        m.address = address
        self._db.flush()
        return _to_entity(m)

    def delete(self, branch_id: UUID) -> bool:
        m = self._db.query(BranchModel).filter(BranchModel.id==branch_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True