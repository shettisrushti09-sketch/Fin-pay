from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class PaymentTransaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)

    wallet_id = Column(
        Integer,
        ForeignKey("wallets.wallet_id"),
        nullable=False
    )

    merchant_id = Column(
        Integer,
        ForeignKey("merchants.merchant_id"),
        nullable=False
    )

    amount_paise = Column(Integer, nullable=False)
    cashback_paise = Column(Integer, nullable=False, default=0)

    idempotency_key = Column(String(100), unique=True, nullable=False)

    transaction_status = Column(String(30), nullable=False)

    transaction_date = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )