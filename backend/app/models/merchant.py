from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(Integer, primary_key=True, index=True)

    merchant_name = Column(String(100), nullable=False)

    category_id = Column(
        Integer,
        ForeignKey("merchant_categories.category_id"),
        nullable=False
    )