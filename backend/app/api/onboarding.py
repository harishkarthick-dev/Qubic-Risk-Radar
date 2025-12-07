"""Onboarding API endpoints"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user, get_verified_user
from app.services.discord_service import discord_service
from app.services.telegram_service import telegram_service
from app.services.email_service import email_service
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# Request/Response models
class OnboardingStatusResponse(BaseModel):
    completed: bool
    current_step: int
    webhook_configured: bool
    webhook_test_received: bool
    notifications_configured: bool
    discord_verified: bool
    telegram_verified: bool


class WebhookConfigRequest(BaseModel):
    alert_id: str
    description: str | None = None


class VerifyDiscordRequest(BaseModel):
    discord_user_id: str


class VerifyTelegramRequest(BaseModel):
    telegram_chat_id: str


class CompleteOnboardingRequest(BaseModel):
    email_notifications_enabled: bool = True


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current onboarding status"""
    # Check if user has any EasyConnect configs
    from app.models.easyconnect_config import EasyConnectConfig
    result = await db.execute(
        select(EasyConnectConfig).where(EasyConnectConfig.user_id == user.id)
    )
    has_webhook = result.scalar_one_or_none() is not None
    
    notifications_configured = user.discord_verified or user.telegram_verified
    
    return {
        "completed": user.onboarding_completed,
        "current_step": user.onboarding_step,
        "webhook_configured": has_webhook,
        "webhook_test_received": user.webhook_test_received,
        "notifications_configured": notifications_configured,
        "discord_verified": user.discord_verified,
        "telegram_verified": user.telegram_verified
    }


@router.post("/webhook")
async def create_webhook_config(
    data: WebhookConfigRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create webhook configuration and get webhook URL
    Step 1 of onboarding
    """
    from app.models.easyconnect_config import EasyConnectConfig
    from app.services.auth import create_verification_token
    
    # Check if alert_id already exists
    result = await db.execute(
        select(EasyConnectConfig).where(
            EasyConnectConfig.user_id == user.id,
            EasyConnectConfig.alert_id == data.alert_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert ID already configured"
        )
    
    # Generate webhook secret
    webhook_secret = create_verification_token()
    
    # Create config
    config = EasyConnectConfig(
        user_id=user.id,
        alert_id=data.alert_id,
        webhook_secret=webhook_secret,
        description=data.description
    )
    
    db.add(config)
    
    # Update onboarding step
    user.onboarding_step = 2
    
    await db.commit()
    await db.refresh(config)
    
    logger.info("webhook_configured_onboarding", user_id=str(user.id), alert_id=data.alert_id)
    
    return {
        "webhook_url": f"{settings.BACKEND_URL}/webhook/qubic/events",
        "webhook_secret": webhook_secret,
        "alert_id": data.alert_id,
        "instructions": "Add this webhook URL to your EasyConnect alert configuration, then send a test notification."
    }


@router.get("/test-status")
async def check_test_status(
    user: User = Depends(get_verified_user)
):
    """Check if test webhook has been received"""
    return {
        "received": user.webhook_test_received,
        "ready_for_next_step": user.webhook_test_received
    }


@router.post("/verify-discord")
async def verify_discord(
    data: VerifyDiscordRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify Discord by sending welcome message"""
    # Save Discord user ID
    user.discord_user_id = data.discord_user_id
    await db.commit()
    
    # Try to send welcome message
    success = await discord_service.send_welcome_message(
        data.discord_user_id,
        user.full_name
    )
    
    if success:
        user.discord_verified = True
        await db.commit()
        
        logger.info("discord_verified_onboarding", user_id=str(user.id), discord_id=data.discord_user_id)
        
        return {
            "success": True,
            "message": "Welcome message sent! Check your Discord DMs.",
            "verified": True
        }
    else:
        return {
            "success": False,
            "error": "Could not send DM. Make sure you have DMs enabled from server members and the user ID is correct."
        }


@router.post("/verify-telegram")
async def verify_telegram(
    data: VerifyTelegramRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify Telegram by sending welcome message"""
    # Save Telegram chat ID
    user.telegram_chat_id = data.telegram_chat_id
    await db.commit()
    
    # Try to send welcome message
    success = await telegram_service.send_welcome_message(
        data.telegram_chat_id,
        user.full_name
    )
    
    if success:
        user.telegram_verified = True
        await db.commit()
        
        logger.info("telegram_verified_onboarding", user_id=str(user.id), chat_id=data.telegram_chat_id)
        
        return {
            "success": True,
            "message": "Welcome message sent! Check your Telegram.",
            "verified": True
        }
    else:
        return {
            "success": False,
            "error": "Could not send message. Make sure you've started a chat with the bot and the chat ID is correct."
        }


@router.post("/complete")
async def complete_onboarding(
    data: CompleteOnboardingRequest,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete onboarding
    Requires: webhook tested AND (discord OR telegram verified)
    """
    # Validation
    if not user.webhook_test_received:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please test your webhook before completing onboarding"
        )
    
    if not (user.discord_verified or user.telegram_verified):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify at least one notification channel (Discord or Telegram)"
        )
    
    # Update user
    user.email_notifications_enabled = data.email_notifications_enabled
    user.onboarding_completed = True
    user.onboarding_step = 4  # Completed
    
    await db.commit()
    
    # Load subscription for email
    await db.refresh(user, ['subscription'])
    
    # Prepare data for email
    trial_end = None
    plan_name = "Pro"
    if user.subscription:
        await db.refresh(user.subscription, ['plan'])
        if user.subscription.plan:
            plan_name = user.subscription.plan.name
        if user.subscription.trial_ends_at:
            trial_end = user.subscription.trial_ends_at.strftime("%B %d, %Y")
    
    # Send completion email
    email_service.send_onboarding_complete_email(
        to_email=user.email,
        full_name=user.full_name,
        user_data={
            'discord_verified': user.discord_verified,
            'telegram_verified': user.telegram_verified,
            'email_enabled': user.email_notifications_enabled,
            'plan_name': plan_name,
            'trial_end': trial_end
        }
    )
    
    logger.info("onboarding_completed", user_id=str(user.id))
    
    # Get active channels
    active_channels = []
    if user.discord_verified:
        active_channels.append("discord")
    if user.telegram_verified:
        active_channels.append("telegram")
    if user.email_notifications_enabled:
        active_channels.append("email")
    
    return {
        "success": True,
        "onboarding_completed": True,
        "active_channels": active_channels
    }
