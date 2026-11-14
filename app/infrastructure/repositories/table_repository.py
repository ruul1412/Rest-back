from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.models.table_model import TableModel
from app.domain.table.table_entity import TableEntity


def _to_entity(m: TableModel) -> TableEntity:
    return TableEntity(
        id=m.id,
        number=m.number,
        capacity=m.capacity,
        status=m.status,
        description=  m.description
    )


class TableRepository:

    def __init__(self, db: Session):
        self._db = db

    def count(self) -> int:
        return self._db.query(TableModel.id).count()

    def get_all_descrip(
        self,
        skip: int = 0,
        limit: int | None = None,
        description: str | None = None
    ) -> list[TableEntity]:

        q = self._db.query(TableModel)

        q = q.filter(TableModel.is_deleted == False)

        if description and description.strip():
            q = q.filter(
                TableModel.description.ilike(f"%{description.strip()}%")
            )

        q = q.order_by(TableModel.number)

        if skip:
            q = q.offset(skip)

        if limit is not None:
            q = q.limit(limit)

        return [_to_entity(m) for m in q.all()]

    def get_all(self, skip: int = 0, limit: int | None = None) -> list[TableEntity]:
        q = self._db.query(TableModel).order_by(TableModel.number)
        if skip:
            q = q.offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return [_to_entity(m) for m in q.all()]

    def get_by_id(self, table_id: UUID) -> Optional[TableEntity]:
        m = self._db.query(TableModel).filter(TableModel.id == table_id).first()
        return _to_entity(m) if m else None

    def number_exists(self, number: int, exclude_id: UUID = None) -> bool:
        q = self._db.query(TableModel.id).filter(TableModel.number == number)
        if exclude_id:
            q = q.filter(TableModel.id != exclude_id)
        return q.first() is not None

    def create(self, number: int, capacity: int, description : str) -> TableEntity:
        m = TableModel(number=number, capacity=capacity, status="libre", description = description)
        self._db.add(m)
        self._db.flush()
        self._db.refresh(m)
        return _to_entity(m)

    def update(self, table_id: UUID, **fields) -> Optional[TableEntity]:
        m = self._db.query(TableModel).filter(TableModel.id == table_id).first()
        if not m:
            return None
        for key, value in fields.items():
            if value is not None:
                setattr(m, key, value)
        self._db.flush()
        return _to_entity(m)

    def update_status(self, table_id: UUID, status: str) -> Optional[TableEntity]:
        m = self._db.query(TableModel).filter(TableModel.id == table_id).first()
        if not m:
            return None
        m.status = status
        self._db.flush()
        return _to_entity(m)

    def delete(self, table_id: UUID) -> bool:
        m = self._db.query(TableModel).filter(TableModel.id == table_id).first()
        if not m:
            return False
        self._db.delete(m)
        self._db.flush()
        return True

    def is_occupied(self, table_id: UUID) -> bool:
        m = self._db.query(TableModel.status).filter(TableModel.id == table_id).first()
        return m and m.status == "ocupada"