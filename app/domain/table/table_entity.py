from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class TableEntity:
    id:       UUID
    number:   int
    capacity: int
    status:   str   # libre | ocupada | reservada | inhabilitada
    description:  Optional[str]