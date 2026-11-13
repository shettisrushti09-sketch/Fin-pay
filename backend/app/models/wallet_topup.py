
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from database import Base


class WalletTopUp(Base):
    __tablename__ = "wallet_topups"

    topup_id = Column(Integer, primary_key=True, index=True)

    wallet_id = Column(
        Integer,
        ForeignKey("wallets.wallet_id"),
        nullable=False
    )

    amount_paise = Column(Integer, nullable=False)

    idempotency_key = Column(
        String(100),
        unique=True,
        nullable=False
    )

    transaction_status = Column(
        String(30),
        nullable=False,
        default="SUCCESS"
    )

    transaction_date = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
