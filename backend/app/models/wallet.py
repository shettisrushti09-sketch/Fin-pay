
from sqlalchemy import Column, Integer, ForeignKey
from database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    wallet_id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.student_id"),
        unique=True,
        nullable=False
    )

    balance_paise = Column(
        Integer,
        nullable=False,
        default=0
    )

    tier_id = Column(
        Integer,
        ForeignKey("wallet_tiers.tier_id"),
        nullable=False
    )

