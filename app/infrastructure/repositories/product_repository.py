from sqlalchemy.orm import Session
from app.infrastructure.models.product_model import ProductModel


class ProductRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, price: float, category_id: str):
        product = ProductModel(
            name=name,
            price=price,
            category_id=category_id
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_all(self):
        return self.db.query(ProductModel).filter(
            ProductModel.is_active == True
            # ProductModel.is_deleted == False
        ).all()

    def get_by_id(self, product_id: str):
        return self.db.query(ProductModel).filter(
            ProductModel.id == product_id
        ).first()