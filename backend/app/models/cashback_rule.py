from sqlalchemy import Column, Integer, Float, ForeignKey
from database import Base


class CashbackRule(Base):
    __tablename__ = "cashback_rules"

    rule_id = Column(Integer, primary_key=True, index=True)

    category_id = Column(
        Integer,
        ForeignKey("merchant_categories.category_id"),
        nullable=False
    )

    base_cashback_rate = Column(Float, nullable=False)

    basic_monthly_cap_paise = Column(Integer, nullable=False)