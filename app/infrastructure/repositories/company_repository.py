
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.company.company_entity import CompanyEntity
from app.infrastructure.models.company_model import CompanyModel


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
        return (
            self._db.query(CompanyModel.id)
            .filter(CompanyModel.is_deleted == False)
            .count()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int | None = None
    ) -> list[CompanyEntity]:

        query = (
            self._db.query(CompanyModel)
            .filter(CompanyModel.is_deleted == False)
            .order_by(CompanyModel.name)
        )

        if skip:
            query = query.offset(skip)

        if limit is not None:
            query = query.limit(limit)

        return [_to_entity(company) for company in query.all()]

    def create(
        self,
        name: str,
        description: Optional[str],
        phone: Optional[str],
        ruc: Optional[str]
    ) -> CompanyEntity:

        company = CompanyModel(
            name=name,
            description=description,
            phone=phone,
            is_active=True,
            ruc=ruc
        )

        self._db.add(company)
        self._db.flush()
        self._db.refresh(company)

        return _to_entity(company)

    def update(
        self,
        company_id: UUID,
        name: Optional[str],
        description: Optional[str],
        phone: Optional[str],
        is_active: bool,
        ruc: Optional[str]
    ) -> Optional[CompanyEntity]:

        company = (
            self._db.query(CompanyModel)
            .filter(
                CompanyModel.id == company_id,
                CompanyModel.is_deleted == False
            )
            .first()
        )

        if not company:
            return None

        company.name = name
        company.description = description
        company.phone = phone
        company.is_active = is_active
        company.ruc = ruc

        self._db.flush()

        return _to_entity(company)

    def updateStatus(
        self,
        company_id: UUID,
        is_active: bool
    ) -> Optional[CompanyEntity]:

        company = (
            self._db.query(CompanyModel)
            .filter(
                CompanyModel.id == company_id,
                CompanyModel.is_deleted == False
            )
            .first()
        )

        if not company:
            return None

        company.is_active = is_active

        self._db.flush()

        return _to_entity(company)

    def delete(self, company_id: UUID) -> bool:

        company = (
            self._db.query(CompanyModel)
            .filter(
                CompanyModel.id == company_id,
                CompanyModel.is_deleted == False
            )
            .first()
        )

        if not company:
            return False

        company.is_active = False
        company.is_deleted = True

        self._db.flush()

        return True

    def name_exists(
        self,
        name: str,
        exclude_id: UUID | None = None
    ) -> bool:

        query = (
            self._db.query(CompanyModel.id)
            .filter(
                func.lower(CompanyModel.name) == name.strip().lower(),
                CompanyModel.is_deleted == False
            )
        )

        if exclude_id:
            query = query.filter(CompanyModel.id != exclude_id)

        return query.first() is not None
