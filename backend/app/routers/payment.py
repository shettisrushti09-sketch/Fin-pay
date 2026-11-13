
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from database import get_db
from app.models.wallet import Wallet
from app.models.wallet_tier import WalletTier
from app.models.merchant import Merchant
from app.models.cashback_rule import CashbackRule
from app.models.payment_transaction import PaymentTransaction
from app.core.auth import get_current_student_id

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


class PaymentCreate(BaseModel):
    merchant_id: int
    amount_paise: int = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=100)


def payment_response(transaction, message="Payment successful"):
    return {
        "message": message,
        "transaction_id": transaction.transaction_id,
        "wallet_id": transaction.wallet_id,
        "merchant_id": transaction.merchant_id,
        "amount_paise": transaction.amount_paise,
        "cashback_paise": transaction.cashback_paise,
        "transaction_status": transaction.transaction_status
    }


# Make a payment
@router.post("/pay")
def make_payment(
    payment: PaymentCreate,
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db)
):
    # Check whether this request was already processed
    existing = db.query(PaymentTransaction).filter(
        PaymentTransaction.idempotency_key == payment.idempotency_key
    ).first()

    if existing:
        if (
            existing.merchant_id == payment.merchant_id
            and existing.amount_paise == payment.amount_paise
            and db.query(Wallet).filter(
                Wallet.wallet_id == existing.wallet_id,
                Wallet.student_id == student_id
            ).first()
        ):
            return payment_response(
                existing,
                "This payment was already processed"
            )

        raise HTTPException(
            status_code=409,
            detail="Idempotency key already used for a different request"
        )

    try:
        # Lock the student's wallet while processing
        wallet = db.query(Wallet).filter(
            Wallet.student_id == student_id
        ).with_for_update().first()

        if not wallet:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        # Check wallet balance
        if wallet.balance_paise < payment.amount_paise:
            raise HTTPException(
                status_code=400,
                detail="Insufficient wallet balance"
            )

        # Find merchant
        merchant = db.query(Merchant).filter(
            Merchant.merchant_id == payment.merchant_id
        ).first()

        if not merchant:
            raise HTTPException(
                status_code=404,
                detail="Merchant not found"
            )

        # Find cashback rule for merchant category
        rule = db.query(CashbackRule).filter(
            CashbackRule.category_id == merchant.category_id
        ).first()

        if not rule:
            raise HTTPException(
                status_code=404,
                detail="Cashback rule not found"
            )

        # Find wallet tier
        tier = db.query(WalletTier).filter(
            WalletTier.tier_id == wallet.tier_id
        ).first()

        if not tier:
            raise HTTPException(
                status_code=404,
                detail="Wallet tier not found"
            )

        # Calculate cashback using tier multiplier
        effective_rate = (
            Decimal(str(rule.base_cashback_rate))
            * Decimal(str(tier.cashback_multiplier))
        )

        raw_cashback = int(
            (
                Decimal(payment.amount_paise)
                * effective_rate
                / Decimal(100)
            ).to_integral_value(rounding=ROUND_FLOOR)
        )

        # Calculate adjusted monthly cashback cap
        adjusted_cap = int(
            Decimal(rule.basic_monthly_cap_paise)
            * Decimal(str(tier.cap_multiplier))
        )

        # Find cashback already earned this month
        current_month = datetime.now().strftime("%Y-%m")

        previous_cashback = db.query(
            func.sum(PaymentTransaction.cashback_paise)
        ).join(
            Merchant,
            PaymentTransaction.merchant_id == Merchant.merchant_id
        ).filter(
            PaymentTransaction.wallet_id == wallet.wallet_id,
            Merchant.category_id == merchant.category_id,
            func.strftime(
                "%Y-%m",
                PaymentTransaction.transaction_date
            ) == current_month,
            PaymentTransaction.transaction_status == "SUCCESS"
        ).scalar() or 0

        # Calculate remaining cap and final cashback
        remaining_cap = max(
            0,
            adjusted_cap - previous_cashback
        )

        final_cashback = min(
            raw_cashback,
            remaining_cap
        )

        # Update wallet balance
        wallet.balance_paise = (
            wallet.balance_paise
            - payment.amount_paise
            + final_cashback
        )

        # Save transaction
        new_transaction = PaymentTransaction(
            wallet_id=wallet.wallet_id,
            merchant_id=merchant.merchant_id,
            amount_paise=payment.amount_paise,
            cashback_paise=final_cashback,
            idempotency_key=payment.idempotency_key,
            transaction_status="SUCCESS"
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return {
            **payment_response(new_transaction),
            "cashback_rupees": final_cashback / 100,
            "new_balance_paise": wallet.balance_paise,
            "new_balance_rupees": wallet.balance_paise / 100
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        # Another request may have used this key at the same time
        existing = db.query(PaymentTransaction).filter(
            PaymentTransaction.idempotency_key == payment.idempotency_key
        ).first()

        if existing:
            if (
                existing.merchant_id == payment.merchant_id
                and existing.amount_paise == payment.amount_paise
                and db.query(Wallet).filter(
                    Wallet.wallet_id == existing.wallet_id,
                    Wallet.student_id == student_id
                ).first()
            ):
                return payment_response(
                    existing,
                    "This payment was already processed"
                )

            raise HTTPException(
                status_code=409,
                detail="Idempotency key already used for a different request"
            )

        raise HTTPException(
            status_code=409,
            detail="Payment could not be completed due to a database conflict"
        )


# View logged-in student's transaction history
@router.get("/history")
def get_payment_history(
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

    records = db.query(
        PaymentTransaction,
        Merchant
    ).join(
        Merchant,
        PaymentTransaction.merchant_id == Merchant.merchant_id
    ).filter(
        PaymentTransaction.wallet_id == wallet.wallet_id
    ).order_by(
        PaymentTransaction.transaction_date.desc()
    ).all()

    return [
        {
            "transaction_id": transaction.transaction_id,
            "merchant_name": merchant.merchant_name,
            "amount_paise": transaction.amount_paise,
            "amount_rupees": transaction.amount_paise / 100,
            "cashback_paise": transaction.cashback_paise,
            "cashback_rupees": transaction.cashback_paise / 100,
            "status": transaction.transaction_status,
            "transaction_date": transaction.transaction_date
        }
        for transaction, merchant in records
    ]

