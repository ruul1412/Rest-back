import enum

class PaymentMethod(str, enum.Enum):
    efectivo      = "efectivo"
    yape          = "yape"
    transferencia = "transferencia"
    mixto = "mixto"

class PaymentStatus(str, enum.Enum):
    pendiente = "pendiente"
    pagado    = "pagado"
    anulado   = "anulado"

class TableStatus(str, enum.Enum):
    libre     = "libre"
    ocupada   = "ocupada"
    reservada = "reservada"