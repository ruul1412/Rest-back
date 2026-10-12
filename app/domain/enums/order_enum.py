import enum

class GroupStatus(str, enum.Enum):
    abierto      = "abierto"
    cerrado      = "cerrado"
    cancelado      = "cancelado"

class OrderStatus(str, enum.Enum):
    pendiente      = "pendiente"
    preparacion = "preparacion"
    listo          = "listo"
    entregado      = "entregado"
    cancelado      = "cancelado"
    
class OrderType(str, enum.Enum):
    mesa     = "mesa"
    llevar = "llevar"
    delivery    = "delivery"