"""Authentication API endpoints"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.plan import Plan, Subscription
from app.services.auth import hash_password, verify_password, create_access_token, create_verification_token
from app.services.email_service import email_service
from app.dependencies.auth import get_current_user, get_verified_user
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    subscription: Optional[dict] = None


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - Creates user account
    - Assigns Pro plan with 30-day trial
    - Sends verification email
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create verification token
    verification_token = create_verification_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Hash password
    password_hash = hash_password(data.password)
    
    # Create user
    user = User(
        email=data.email,
        password_hash=password_hash,
        full_name=data.full_name,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=verification_expires
    )
    db.add(user)
    await db.flush()  # Get user.id
    
    # Get Pro plan
    pro_plan_result = await db.execute(
        select(Plan).where(Plan.name == "Pro")
    )
    pro_plan = pro_plan_result.scalar_one_or_none()
    
    if not pro_plan:
        # Create Pro plan if it doesn't exist (fallback)
        pro_plan = Plan(
            name="Pro",
            price_monthly=0,
            price_yearly=0,
            max_alerts=200,
            max_rules=50,
            max_monitored_contracts=20,
            features_json={
                "discord_notifications": True,
                "telegram_notifications": True,
                "email_notifications": True,
                "webhook_history_days": 30,
                "advanced_rules": True,
                "api_access": True
            }
        )
        db.add(pro_plan)
        await db.flush()
    
    # Create subscription with trial or unlimited based on pricing mode
    if settings.PRICING_ENABLED:
        # Trial mode: 30-day Pro trial
        subscription = Subscription(
            user_id=user.id,
            plan_id=pro_plan.id,
            status="trial",
            trial_ends_at=datetime.utcnow() + timedelta(days=settings.PRO_TRIAL_DAYS)
        )
    else:
        # Free mode: Unlimited Pro access
        subscription = Subscription(
            user_id=user.id,
            plan_id=pro_plan.id,
            status="active",  # Active, not trial
            trial_ends_at=None  # No expiration
        )
    db.add(subscription)
    
    await db.commit()
    
    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=user.email,
        full_name=user.full_name,
        verification_token=verification_token
    )
    
    if not email_sent:
        logger.error("verification_email_failed", user_id=str(user.id), email=user.email)
    
    logger.info("user_registered", user_id=str(user.id), email=user.email)
    
    return {
        "user_id": str(user.id),
        "message": f"Verification email sent to {user.email}. Please check your inbox and verify your account."
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    - Returns JWT access token
    - Requires email verification
    """
    # Find user by email (username field in OAuth2 form)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email and verify your account."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(str(user.id))
    
    logger.info("user_logged_in", user_id=str(user.id), email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified
        }
    }


@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., description="Verification token from email"),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email with token
    
    - Marks email as verified
    - Sends welcome email
    """
    # Find user with this verification token
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Check if token expired
    if user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired. Please request a new one."
        )
    
    # Verify user
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    await db.commit()
    
    # Send welcome email
    email_service.send_welcome_email(
        to_email=user.email,
        full_name=user.full_name
    )
    
    logger.info("email_verified", user_id=str(user.id), email=user.email)
    
    return {
        "message": "Email verified successfully! You can now log in."
    }


@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend verification email
    
    - Generates new token
    - Sends new email
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification email has been sent."}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new token
    verification_token = create_verification_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    
    await db.commit()
    
    # Send email
    email_service.send_verification_email(
        to_email=user.email,
        full_name=user.full_name,
        verification_token=verification_token
    )
    
    logger.info("verification_resent", user_id=str(user.id), email=user.email)
    
    return {"message": "Verification email sent. Please check your inbox."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile
    
    - Returns user info
    - Includes subscription details
    """
    # Load subscription with plan
    await db.refresh(user, ['subscription'])
    
    subscription_data = None
    if user.subscription:
        await db.refresh(user.subscription, ['plan'])
        subscription_data = {
            "plan": user.subscription.plan.name if user.subscription.plan else "Free",
            "status": user.subscription.status,
            "trial_ends_at": user.subscription.trial_ends_at.isoformat() if user.subscription.trial_ends_at else None,
            "next_billing_date": user.subscription.next_billing_date.isoformat() if user.subscription.next_billing_date else None
        }
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "subscription": subscription_data
    }
