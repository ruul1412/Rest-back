from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: UUID
    code: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class UserPermissionResponse(BaseModel):
    """Permiso directo de un usuario, con metadata de auditoría."""
    id: UUID
    code: str
    description: Optional[str] = None
    granted_by: UUID
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class AssignPermissionsRequest(BaseModel):
    permission_codes: list[str]
    granted_by: UUID          # quién otorga (el admin autenticado)
    expires_at: Optional[datetime] = None   # None = permanente
    reason: Optional[str] = None


class RevokePermissionRequest(BaseModel):
    permission_code: str