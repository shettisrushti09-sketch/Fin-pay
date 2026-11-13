
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from app.models.student import Student
from app.models.wallet import Wallet
from app.models.wallet_tier import WalletTier
from app.schemas.student import StudentCreate, StudentLogin, StudentResponse
from app.core.security import hash_password, verify_password
from app.core.auth import create_access_token

router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


# Student Registration with Automatic Wallet Creation
@router.post("/register", response_model=StudentResponse)
def register_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    existing_student = db.query(Student).filter(
        Student.email == student.email
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Find the Basic wallet tier
    basic_tier = db.query(WalletTier).filter(
        WalletTier.tier_name == "Basic"
    ).first()

    # Create Basic tier if it does not exist
    if not basic_tier:
        basic_tier = WalletTier(
            tier_name="Basic",
            cashback_multiplier=1.0,
            cap_multiplier=1.0
        )
        db.add(basic_tier)
        db.flush()

    # Hash student password
    hashed_password = hash_password(student.password)

    # Create student
    new_student = Student(
        student_name=student.student_name,
        email=student.email,
        password=hashed_password
    )

    db.add(new_student)
    db.flush()

    # Automatically create wallet
    new_wallet = Wallet(
        student_id=new_student.student_id,
        balance_paise=0,
        tier_id=basic_tier.tier_id
    )

    db.add(new_wallet)
    db.commit()
    db.refresh(new_student)

    return new_student


# Student Login
@router.post("/login")
def login_student(
    student: StudentLogin,
    db: Session = Depends(get_db)
):
    existing_student = db.query(Student).filter(
        Student.email == student.email
    ).first()

    if not existing_student:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        student.password,
        existing_student.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "sub": str(existing_student.student_id)
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "student_id": existing_student.student_id,
        "student_name": existing_student.student_name
    }
