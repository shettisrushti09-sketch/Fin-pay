from sqlalchemy import Column, Integer, String, Float
from database import Base


class WalletTier(Base):
    __tablename__ = "wallet_tiers"

    tier_id = Column(Integer, primary_key=True, index=True)
    tier_name = Column(String(50), unique=True, nullable=False)
    cashback_multiplier = Column(Float, nullable=False, default=1.0)
    cap_multiplier = Column(Float, nullable=False, default=1.0)