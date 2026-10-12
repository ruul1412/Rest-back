# app/domain/permission/permission_entity.py
from uuid import UUID
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class PermissionEntity:
    id: UUID
    code: str
    description: Optional[str] = None


@dataclass
class UserPermissionEntity:
    """Permiso directo asignado a un usuario, con metadata de auditoría."""
    id: UUID
    code: str
    description: Optional[str] = None
    granted_by: UUID = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None