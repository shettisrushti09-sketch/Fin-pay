
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from app.models.merchant_category import MerchantCategory
from app.models.merchant import Merchant

router = APIRouter(
    prefix="/merchants",
    tags=["Merchants"]
)


class CategoryCreate(BaseModel):
    category_name: str


class MerchantCreate(BaseModel):
    merchant_name: str
    category_id: int


# Add a merchant category
@router.post("/categories")
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(MerchantCategory).filter(
        MerchantCategory.category_name == category.category_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Category already exists"
        )

    new_category = MerchantCategory(
        category_name=category.category_name
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return {
        "message": "Category created successfully",
        "category_id": new_category.category_id,
        "category_name": new_category.category_name
    }


# View all categories
@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(MerchantCategory).all()


# Add a merchant
@router.post("/")
def create_merchant(
    merchant: MerchantCreate,
    db: Session = Depends(get_db)
):
    category = db.query(MerchantCategory).filter(
        MerchantCategory.category_id == merchant.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    new_merchant = Merchant(
        merchant_name=merchant.merchant_name,
        category_id=merchant.category_id
    )

    db.add(new_merchant)
    db.commit()
    db.refresh(new_merchant)

    return {
        "message": "Merchant created successfully",
        "merchant_id": new_merchant.merchant_id,
        "merchant_name": new_merchant.merchant_name,
        "category": category.category_name
    }


# View all merchants
@router.get("/")
def get_merchants(db: Session = Depends(get_db)):
    return db.query(Merchant).all()
