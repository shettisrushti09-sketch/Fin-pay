
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db
from app.models.cashback_rule import CashbackRule
from app.models.merchant_category import MerchantCategory

router = APIRouter(
    prefix="/cashback",
    tags=["Cashback Rules"]
)


class CashbackRuleCreate(BaseModel):
    category_id: int
    base_cashback_rate: float = Field(ge=0, le=100)
    basic_monthly_cap_paise: int = Field(ge=0)


# Create cashback rule
@router.post("/rules")
def create_cashback_rule(
    rule: CashbackRuleCreate,
    db: Session = Depends(get_db)
):
    category = db.query(MerchantCategory).filter(
        MerchantCategory.category_id == rule.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    existing_rule = db.query(CashbackRule).filter(
        CashbackRule.category_id == rule.category_id
    ).first()

    if existing_rule:
        raise HTTPException(
            status_code=409,
            detail="Cashback rule already exists"
        )

    new_rule = CashbackRule(
        category_id=rule.category_id,
        base_cashback_rate=rule.base_cashback_rate,
        basic_monthly_cap_paise=rule.basic_monthly_cap_paise
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return {
        "message": "Cashback rule created successfully",
        "rule_id": new_rule.rule_id,
        "category": category.category_name,
        "cashback_rate": new_rule.base_cashback_rate,
        "monthly_cap_paise": new_rule.basic_monthly_cap_paise
    }


# View all cashback rules
@router.get("/rules")
def get_cashback_rules(db: Session = Depends(get_db)):
    return db.query(CashbackRule).all()
