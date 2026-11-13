
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from database import get_db
from app.models.wallet import Wallet
from app.models.wallet_tier import WalletTier
from app.models.wallet_topup import WalletTopUp
from app.core.auth import get_current_student_id

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)


class WalletTopUpCreate(BaseModel):
    amount_paise: int = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=100)


# View logged-in student's wallet
@router.get("/me")
def get_my_wallet(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db)
):
    wallet = db.query(Wallet).filter(
        Wallet.student_id == student_id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    tier = db.query(WalletTier).filter(
        WalletTier.tier_id == wallet.tier_id
    ).first()

    return {
        "wallet_id": wallet.wallet_id,
        "student_id": wallet.student_id,
        "balance_paise": wallet.balance_paise,
        "balance_rupees": wallet.balance_paise / 100,
        "tier": tier.tier_name if tier else None
    }


# Add money to wallet without cashback
@router.post("/top-up")
def top_up_wallet(
    data: WalletTopUpCreate,
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db)
):
    wallet = db.query(Wallet).filter(
        Wallet.student_id == student_id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    existing = db.query(WalletTopUp).filter(
        WalletTopUp.idempotency_key == data.idempotency_key
    ).first()

    if existing:
        if (
            existing.wallet_id == wallet.wallet_id
            and existing.amount_paise == data.amount_paise
        ):
            return {
                "message": "Top-up already processed",
                "topup_id": existing.topup_id,
                "amount_paise": existing.amount_paise,
                "cashback_paise": 0,
                "balance_paise": wallet.balance_paise
            }

        raise HTTPException(
            status_code=409,
            detail="Idempotency key already used"
        )

    try:
        wallet.balance_paise += data.amount_paise

        topup = WalletTopUp(
            wallet_id=wallet.wallet_id,
            amount_paise=data.amount_paise,
            idempotency_key=data.idempotency_key,
            transaction_status="SUCCESS"
        )

        db.add(topup)
        db.commit()
        db.refresh(topup)

        return {
            "message": "Wallet topped up successfully",
            "topup_id": topup.topup_id,
            "amount_paise": topup.amount_paise,
            "amount_rupees": topup.amount_paise / 100,
            "cashback_paise": 0,
            "new_balance_paise": wallet.balance_paise,
            "new_balance_rupees": wallet.balance_paise / 100
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Duplicate top-up request"
        )
