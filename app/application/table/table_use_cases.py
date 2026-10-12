from uuid import UUID

from fastapi import HTTPException

from app.interfaces.schemas.table_schema import (
    TableCreateRequest, TableUpdateRequest,
    TableStatusRequest, TableResponse,
)
from app.infrastructure.repositories.table_repository import TableRepository


def _resp(e) -> TableResponse:
    return TableResponse(id=e.id, number=e.number, capacity=e.capacity, status=e.status)


class ListTablesUseCase:
    def __init__(self, repo: TableRepository): self._repo = repo

    def execute(self) -> list[TableResponse]:
        return [_resp(e) for e in self._repo.get_all()]


class CreateTableUseCase:
    def __init__(self, repo: TableRepository): self._repo = repo

    def execute(self, data: TableCreateRequest) -> TableResponse:
        if self._repo.number_exists(data.number):
            raise HTTPException(status_code=400, detail=f"Ya existe la mesa número {data.number}")
        return _resp(self._repo.create(data.number, data.capacity))


class UpdateTableUseCase:
    def __init__(self, repo: TableRepository): self._repo = repo

    def execute(self, table_id: UUID, data: TableUpdateRequest) -> TableResponse:
        if data.number and self._repo.number_exists(data.number, exclude_id=table_id):
            raise HTTPException(status_code=400, detail=f"Ya existe la mesa número {data.number}")
        entity = self._repo.update(table_id, number=data.number, capacity=data.capacity)
        if not entity:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        return _resp(entity)


class UpdateTableStatusUseCase:
    def __init__(self, repo: TableRepository): self._repo = repo

    def execute(self, table_id: UUID, data: TableStatusRequest) -> TableResponse:
        entity = self._repo.update_status(table_id, data.status)
        if not entity:
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        return _resp(entity)


class DeleteTableUseCase:
    def __init__(self, repo: TableRepository): self._repo = repo

    def execute(self, table_id: UUID) -> dict:
        if self._repo.is_occupied(table_id):
            raise HTTPException(status_code=400, detail="No se puede eliminar una mesa ocupada")
        if not self._repo.delete(table_id):
            raise HTTPException(status_code=404, detail="Mesa no encontrada")
        return {"detail": "Mesa eliminada"}