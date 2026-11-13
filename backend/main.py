
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# Import database models
from app.models.student import Student
from app.models.wallet_tier import WalletTier
from app.models.merchant_category import MerchantCategory
from app.models.cashback_rule import CashbackRule
from app.models.merchant import Merchant
from app.models.wallet import Wallet
from app.models.payment_transaction import PaymentTransaction
from app.models.wallet_topup import WalletTopUp

# Import API routers
from app.routers.student import router as student_router
from app.routers.wallet import router as wallet_router
from app.routers.merchant import router as merchant_router
from app.routers.cashback import router as cashback_router
from app.routers.payment import router as payment_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI application
app = FastAPI(
    title="FinPay API",
    description="Digital Wallet and Cashback Management System",
    version="1.0"
)


# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(student_router)
app.include_router(wallet_router)
app.include_router(merchant_router)
app.include_router(cashback_router)
app.include_router(payment_router)


# Home route
@app.get("/")
def home():
    return {
        "message": "Welcome to FinPay!",
        "status": "Backend is running"
    }


# Health check route
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "FinPay"
    }
