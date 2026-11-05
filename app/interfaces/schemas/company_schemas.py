from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class CompanyCreateRequest(BaseModel):

    description : str
    phone : str
    is_active : bool
    name :Optional[str]=None
    ruc : str

class CompanyResponse(CompanyCreateRequest):
    id: UUID     