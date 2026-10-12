import enum
 
class ProductType(str, enum.Enum):

    # Define el COMPORTAMIENTO del producto en el sistema.
    # No confundir con category (organización visual del menú).
 
    # plato     → se cocina en cocina, descuenta ingredientes
    # bebida    → viene de barra/almacén, puede tener talla
    # adicional → depende de otro producto (extra queso, ají)
    # combo     → agrupa productos hijos, tiene composición interna
    # menu      → precio fijo, requiere selección de entrada + fondo
    
    menu      = "menu"
    carta     = "carta"
    entrada   = "entrada"
    adicional = "adicional"
    bebida    = "bebida"
    postre    = "postre"
