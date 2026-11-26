from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.branch.branch_entity import BranchEntity
from app.infrastructure.models.branch_model import BranchModel
from app.domain.table.table_entity import TableEntity
from app.infrastructure.models.company_model import CompanyModel


def _to_entity(m: BranchModel) -> BranchEntity:
    return BranchEntity(
        id=m.id,
        name=m.name,
        description=m.description,
        phone=m.phone,
        address=m.address,
        is_active=m.is_active,
        company_name = m.company.name
    )

class BranchRepository:

    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        return self._db.query(BranchModel.id).filter(BranchModel.is_deleted == False).count()

    def get_all(self, skip: int = 0, limit: int | None = None) -> list[BranchEntity]:
        q = self._db.query(BranchModel).join(BranchModel.company).order_by(BranchModel.name)
        if skip:
            q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        
        return [_to_entity(m) for m in q.all()]

    #_________________
    def get_by_company(self, company_id: UUID, skip: int = 0, limit: int | None = None) -> list[BranchEntity]:
            q = self._db.query(BranchModel).filter(BranchModel.company_id == company_id).filter(BranchModel.is_deleted == False).order_by(BranchModel.name)
            if skip:
                q = q.offset(skip)
            if limit is not None:
                q = q.limit(limit)
            return [_to_entity(m) for m in q.all()]

    #------------------contar por compania-----------------------
    def count_by_company(self, company_id: UUID) -> int:
        return self._db.query(BranchModel.id).filter(BranchModel.is_deleted == False).filter(BranchModel.company_id == company_id).count()

    def create(self, name: str, description: Optional[str], phone: Optional[str], address: str, company_id: UUID) -> BranchEntity: 
        m=BranchModel(name=name, description=description, phone=phone,address=address, company_id=company_id)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _to_entity(m)

    def update(
        self,
        branch_id: UUID,
        name: Optional[str],
        description: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        is_active: Optional[bool] = None,
    ) -> Optional[BranchEntity]:

        m = (
            self._db.query(BranchModel)
            .filter(BranchModel.id == branch_id)
            .first()
        )

        if not m:
            return None

        m.name = name
        m.description = description
        m.phone = phone
        m.address = address

        if is_active is not None:
            m.is_active = is_active

        self._db.flush()

        return _to_entity(m)

    def updateStatus(self, branch_id: UUID, is_active: bool) -> Optional[BranchEntity]:
            m = self._db.query(BranchModel).filter(BranchModel.id==branch_id).first()
            if not m:
                return None
            m.is_active = is_active
            self._db.flush()
            return _to_entity(m)

    def delete(self, branch_id: UUID) -> bool:
        m = self._db.query(BranchModel).filter(BranchModel.id==branch_id).first()
        if not m:
            return False   
        m.is_active = False
        m.is_deleted= True
        self._db.flush()
        return True

