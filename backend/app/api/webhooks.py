"""Webhook endpoint for EasyConnect integration with AI Detection"""
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.event import Event, NormalizedEvent
from app.models.ai_detection import AIDetection, Incident
from app.models.easyconnect_config import EasyConnectConfig
from app.models.user import User
from app.services.event_normalizer import EventNormalizer
from app.services.ai_detection_engine import ai_detection_engine
from app.services.classification_engine import classification_engine
from app.services.notifications.discord import DiscordNotificationService
from app.services.notifications.telegram import TelegramNotificationService
from app.services.notifications.email import EmailNotificationService
from app.logging_config import get_logger
from app.config import settings
from datetime import datetime

router = APIRouter(prefix="/webhook", tags=["webhooks"])
logger = get_logger(__name__)


def verify_webhook_signature(body: bytes, signature: str | None) -> bool:
    """
    Verify HMAC signature from EasyConnect webhook
    
    Args:
        body: Raw request body
        signature: X-Signature header value
        
    Returns:
        True if signature is valid
    """
    if not signature or not settings.WEBHOOK_SECRET:
        return True  # Skip verification if not configured
    
    try:
        expected = hmac.new(
            key=settings.WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error("signature_verification_failed", error=str(e))
        return False


@router.post("/qubic/events")
async def receive_qubic_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str | None = Header(None, alias="X-Signature")
):
    """
    Receive and process events from EasyConnect webhooks with AI Detection
    
    This endpoint (Next-Gen):
    1. Verifies webhook signature
    2. Stores raw event payload
    3. Normalizes event data
    4. Analyzes with AI Detection Engine (Gemini)
    5. Auto-classifies and categorizes
    6. Creates incidents if warranted
    7. Routes notifications based on severity
    
    Request Body (from EasyConnect):
    {
        "alert_id": "uuid",
        "event_type": "Transfer",
        "contract_address": "...",
        "contract_name": "QX",
        "tx_hash": "...",
        "tick": 12345,
        "timestamp": "2025-12-06T11:30:00Z",
        "status": "success",
        "from_address": "...",
        "to_address": "...",
        "amount": 5000000,
        "token_symbol": "QUBIC"
    }
    
    Returns:
        200: Event processed successfully
        401: Invalid signature
        500: Processing error
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(body, x_signature):
        logger.warning("invalid_webhook_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("invalid_json_payload", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info("webhook_received", alert_id=payload.get("alert_id"))
    
    try:
        # Get EasyConnect config to find user
        alert_id = payload.get("alert_id")
        if not alert_id:
            raise HTTPException(status_code=400, detail="Missing alert_id")
        
        result = await db.execute(
            select(EasyConnectConfig).where(EasyConnectConfig.alert_id == alert_id)
        )
        ec_config = result.scalar_one_or_none()
        
        if not ec_config:
            logger.warning("unknown_alert_id", alert_id=alert_id)
            raise HTTPException(status_code=404, detail="Alert ID not found")
        
        # Update webhook test status for onboarding
        user_result = await db.execute(
            select(User).where(User.id == ec_config.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if user and not user.webhook_test_received:
            user.webhook_test_received = True
            await db.commit()
            logger.info("webhook_test_received", user_id=str(user.id))
        
        # 1. Store raw event
        event = Event(
            user_id=ec_config.user_id,
            easyconnect_config_id=ec_config.id,
            raw_payload=payload,
            event_type=payload.get("event_type", "Unknown")
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        logger.info("event_stored", event_id=str(event.id))
        
        # 2. Normalize event
        normalizer = EventNormalizer()
        normalized = await normalizer.normalize(event, db)
        
        if not normalized:
            logger.error("normalization_failed", event_id=str(event.id))
            return {"status": "error", "message": "Event normalization failed"}
        
        logger.info("event_normalized", normalized_id=str(normalized.id))
        
        # 3. AI Detection Analysis
        detection = await ai_detection_engine.analyze_event(normalized, db)
        
        if not detection:
            logger.warning("ai_analysis_skipped", event_id=str(event.id))
            return {
                "status": "accepted",
                "message": "Event stored (AI analysis unavailable)",
                "event_id": str(event.id)
            }
        
        logger.info(
            "ai_analysis_complete",
            detection_id=str(detection.id),
            severity=detection.severity,
            anomaly_score=detection.anomaly_score,
            category=detection.primary_category
        )
        
        # 4. Classification
        classification = classification_engine.classify(detection, normalized)
        
        # Update detection with classification results
        detection.sub_categories = classification['sub_categories']
        detection.scope = classification['scope']
        await db.commit()
        
        # 5. Create incident if warranted
        incident = None
        if classification_engine.should_create_incident(detection):
            incident = Incident(
                detection_id=detection.id,
                user_id=ec_config.user_id,
                title=detection.summary[:255],
                severity=detection.severity,
                category=detection.primary_category,
                scope=detection.scope,
                first_detected_at=normalized.timestamp or datetime.utcnow(),
                impact_score=detection.anomaly_score,
                urgency='high' if detection.severity == 'CRITICAL' else 'moderate',
                tags=classification['tags']
            )
            db.add(incident)
            await db.commit()
            await db.refresh(incident)
            
            logger.info(
                "incident_created",
                incident_id=str(incident.id),
                severity=incident.severity
           )
            
            # 6. Send notifications (minimal format)
            await send_notifications(incident, detection, user, db)
        
        return {
            "status": "success",
            "message": "Event processed with AI detection",
            "event_id": str(event.id),
            "detection_id": str(detection.id),
            "incident_id": str(incident.id) if incident else None,
            "severity": detection.severity,
            "anomaly_score": detection.anomaly_score,
            "category": detection.primary_category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


async def send_notifications(
    incident: Incident,
    detection: AIDetection,
    user: User,
    db: AsyncSession
):
    """
    Send minimal notifications based on severity
    
    Routes notifications to configured channels:
    - CRITICAL: Discord, Telegram, Email
    - HIGH: Discord, Telegram
    - MEDIUM: Telegram
    - LOW: Email (digest)
    """
    try:
        # Get key metrics for minimal notification
        event_result = await db.execute(
            select(NormalizedEvent).where(NormalizedEvent.id == detection.event_id)
        )
        event = event_result.scalar_one_or_none()
        
        if not event:
            return
        
        # Extract key info
        amount = event.data.get('amount', 0) if event.data else 0
        category = detection.primary_category
        severity = detection.severity
        
        # Format minimal message
        message_parts = [
            f"{'🔴' if severity == 'CRITICAL' else '🟠' if severity == 'HIGH' else '🔵' if severity == 'MEDIUM' else '🟢'} {severity} ALERT",
            f"\n{category}",
            f"\n💰 {amount:,.0f} QUBIC" if amount > 0 else "",
            f"\n⏰ Just now",
            f"\n\n[View Details →]"
        ]
        minimal_message = ''.join(filter(None, message_parts))
        
        # Route based on severity
        if severity == 'CRITICAL':
            # Send to all channels
            if user.discord_verified:
                discord = DiscordNotificationService()
                await discord.send_alert(
                    user_id=user.discord_user_id,
                    title=f"🔴 {category}",
                    message=minimal_message,
                    severity="critical"
                )
            
            if user.telegram_verified:
                telegram = TelegramNotificationService()
                await telegram.send_alert(
                    chat_id=user.telegram_chat_id,
                    message=minimal_message
                )
            
            if user.email_notifications_enabled:
                email = EmailNotificationService()
                await email.send_detection_alert(
                    to_email=user.email,
                    detection=detection,
                    user=user
                )
        
        elif severity == 'HIGH':
            # Discord + Telegram
            if user.discord_verified:
                discord = DiscordNotificationService()
                await discord.send_alert(
                    user_id=user.discord_user_id,
                    title=f"🟠 {category}",
                    message=minimal_message,
                    severity="warning"
                )
            
            if user.telegram_verified:
                telegram = TelegramNotificationService()
                await telegram.send_alert(
                    chat_id=user.telegram_chat_id,
                    message=minimal_message
                )
        
        elif severity == 'MEDIUM':
            # Telegram only
            if user.telegram_verified:
                telegram = TelegramNotificationService()
                await telegram.send_alert(
                    chat_id=user.telegram_chat_id,
                    message=minimal_message
                )
        
        # LOW and INFO: batched/digest (handled separately)
        
        logger.info(
            "notifications_sent",
            incident_id=str(incident.id),
            severity=severity
        )
        
    except Exception as e:
        logger.error("notification_send_error", error=str(e))
        # Don't fail the whole request if notifications fail


@router.get("/health")
async def webhook_health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_detection_enabled": ai_detection_engine.enabled,
        "model": settings.GEMINI_MODEL if ai_detection_engine.enabled else None
    }



def verify_webhook_signature(body: bytes, signature: str | None) -> bool:
    """
    Verify HMAC signature from EasyConnect webhook
    
    Args:
        body: Raw request body
        signature: X-Signature header value
        
    Returns:
        True if signature is valid
    """
    if not signature or not settings.WEBHOOK_SECRET:
        return True  # Skip verification if not configured
    
    try:
        expected = hmac.new(
            key=settings.WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error("signature_verification_failed", error=str(e))
        return False


@router.post("/qubic/events")
async def receive_qubic_event(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str | None = Header(None, alias="X-Signature")
):
    """
    Receive and process events from EasyConnect webhooks
    
    This endpoint:
    1. Verifies webhook signature
    2. Stores raw event payload
    3. Normalizes event data
    4. Evaluates against detection rules
    5. Creates incidents if rules trigger
    6. Sends notifications for critical incidents
    
    Request Body (from EasyConnect):
    {
        "alert_id": "uuid",
        "event_type": "Transfer",
        "contract_address": "...",
        "contract_name": "QX",
        "tx_hash": "...",
        "tick": 12345,
        "timestamp": "2025-12-06T11:30:00Z",
        "status": "success",
        "from_address": "...",
        "to_address": "...",
        "amount": 5000000,
        "token_symbol": "QUBIC"
    }
    
    Returns:
        200: Event processed successfully
        401: Invalid signature
        500: Processing error
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(body, x_signature):
        logger.warning("invalid_webhook_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("invalid_json_payload", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(
        "webhook_received",
        alert_id=payload.get('alert_id'),
        event_type=payload.get('event_type'),
        contract=payload.get('contract_name')
    )
    
    # Store raw event
    source = f"easyconnect:{payload.get('alert_id', 'unknown')}"
    event = Event(
        source=source,
        payload_json=payload,
        signature=x_signature,
        status='pending'
    )
    db.add(event)
    await db.flush()
    
    # Check if this is a test webhook for onboarding
    # Find user by alert_id from EasyConnect config
    from app.models.easyconnect_config import EasyConnectConfig
    from app.models.user import User
    from sqlalchemy import select
    
    alert_id = payload.get('alert_id')
    if alert_id:
        result = await db.execute(
            select(EasyConnectConfig).where(EasyConnectConfig.alert_id == alert_id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            # Check if user is in onboarding and hasn't tested webhook yet
            result = await db.execute(
                select(User).where(User.id == config.user_id)
            )
            user = result.scalar_one_or_none()
            
            if user and not user.webhook_test_received:
                user.webhook_test_received = True
                user.onboarding_step = 3  # Move to notifications step
                await db.flush()
                logger.info("onboarding_webhook_test_received", user_id=str(user.id), alert_id=alert_id)
    
    try:
        # Normalize event
        normalizer = EventNormalizer()
        normalized_data = normalizer.normalize_easyconnect_payload(payload)
        
        normalized_event = NormalizedEvent(
            event_id=event.id,
            **normalized_data
        )
        db.add(normalized_event)
        await db.flush()
        
        event.status = 'parsed'
        
        # Evaluate rules
        rule_engine = RuleEngine(db)
        incidents = await rule_engine.evaluate_event(normalized_event)
        
        # Send notifications for new incidents
        if incidents:
            logger.info("incidents_created", count=len(incidents))
            
            for incident in incidents:
                # Send notifications asynchronously (don't block webhook response)
                try:
                    # Discord
                    if settings.DISCORD_WEBHOOK_URL_CRITICAL or settings.DISCORD_WEBHOOK_URL_WARNING:
                        discord = DiscordNotificationService(db)
                        await discord.send_with_retry(incident)
                    
                    # Telegram
                    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                        telegram = TelegramNotificationService(db)
                        await telegram.send_with_retry(incident)
                    
                    # Email (only for CRITICAL)
                    if incident.severity == 'CRITICAL' and settings.SENDGRID_API_KEY:
                        email = EmailNotificationService(db)
                        await email.send_with_retry(incident)
                        
                except Exception as e:
                    logger.error("notification_error", incident_id=str(incident.id), error=str(e))
        
        await db.commit()
        
        return {
            "status": "success",
            "event_id": str(event.id),
            "normalized_event_id": str(normalized_event.id),
            "incidents_created": len(incidents)
        }
        
    except Exception as e:
        event.status = 'failed'
        await db.commit()
        
        logger.error("webhook_processing_failed", event_id=str(event.id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/health")
async def webhook_health():
    """Webhook endpoint health check"""
    return {"status": "healthy", "service": "webhook_ingestion"}
