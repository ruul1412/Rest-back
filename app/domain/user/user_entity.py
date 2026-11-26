
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class BranchAssignmentEntity:
    branch_id: UUID
    branch_name: str
    company_name: Optional[str] = None
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False


@dataclass
class UserEntity:
    id: UUID
    email: str
    password: str

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None

    # Estado global de la cuenta
    is_active: bool = True
    is_deleted: bool = False

    # Rol correspondiente al contexto consultado
    role_code: Optional[str] = None
    role_name: Optional[str] = None

    # Estado de la asignación a una sucursal
    branch_is_active: Optional[bool] = None
    branch_is_deleted: Optional[bool] = None

    # Asignaciones del usuario a sucursales
    assignments: list[BranchAssignmentEntity] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email
