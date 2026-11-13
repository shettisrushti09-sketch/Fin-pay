from sqlalchemy import Column, Integer, String
from database import Base


class MerchantCategory(Base):
    __tablename__ = "merchant_categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)