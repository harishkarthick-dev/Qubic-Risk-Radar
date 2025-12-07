"""API endpoints for managing multiple webhooks"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel

from app.database import get_db
from app.models.easyconnect_config import EasyConnectConfig
from app.models.user import User
from app.api.auth import get_verified_user
from app.logging_config import get_logger
from app.config import settings
import secrets

router = APIRouter(prefix="/api/webhooks", tags=["webhooks-management"])
logger = get_logger(__name__)


# Pydantic models
class WebhookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    alert_id: str
    tags: Optional[List[str]] = None
    webhook_priority: int = 0
    is_primary: bool = False
    routing_rule_id: Optional[str] = None


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    webhook_priority: Optional[int] = None
    is_primary: Optional[bool] = None
    routing_rule_id: Optional[str] = None
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: str
    name: Optional[str]
    description: Optional[str]
    alert_id: str
    webhook_url: str
    tags: Optional[List[str]]
    webhook_priority: int
    is_primary: bool
    routing_rule_id: Optional[str]
    enabled: bool
    created_at: datetime
    last_event_at: Optional[datetime]
    total_events: int
    
    class Config:
        from_attributes = True


class WebhookStats(BaseModel):
    total_webhooks: int
    active_webhooks: int
    total_events: int
    events_today: int
    by_tag: dict


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    tag: Optional[str] = Query(None),
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all webhook configurations for the authenticated user
    
    Query Parameters:
    - tag: Filter by tag
    """
    try:
        conditions = [EasyConnectConfig.user_id == user.id]
        
        # Filter by tag if provided
        if tag:
            conditions.append(EasyConnectConfig.tags.contains([tag]))
        
        query = (
            select(EasyConnectConfig)
            .where(and_(*conditions))
            .order_by(
                desc(EasyConnectConfig.is_primary),
                desc(EasyConnectConfig.webhook_priority),
                desc(EasyConnectConfig.created_at)
            )
        )
        
        result = await db.execute(query)
        webhooks = result.scalars().all()
        
        # Enrich with stats (simplified - would normally query events table)
        response = []
        for webhook in webhooks:
            response.append(WebhookResponse(
                id=str(webhook.id),
                name=webhook.name,
                description=webhook.description,
                alert_id=webhook.alert_id,
                webhook_url=f"{settings.BACKEND_URL}/webhook/qubic/events",
                tags=webhook.tags or [],
                webhook_priority=webhook.webhook_priority,
                is_primary=webhook.is_primary,
                routing_rule_id=str(webhook.routing_rule_id) if webhook.routing_rule_id else None,
                enabled=webhook.enabled if hasattr(webhook, 'enabled') else True,
                created_at=webhook.created_at,
                last_event_at=None,  # Would query from events
                total_events=0  # Would query from events
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    webhook_data: WebhookCreate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook configuration
    
    Generates webhook URL and secret for EasyConnect integration
    """
    try:
        from app.config import settings
        
        # Generate webhook secret
        webhook_secret = secrets.token_urlsafe(32)
        
        # If this is marked as primary, unmark others
        if webhook_data.is_primary:
            await db.execute(
                select(EasyConnectConfig)
                .where(EasyConnectConfig.user_id == user.id)
                .execution_options(synchronize_session=False)
            )
            result = await db.execute(
                select(EasyConnectConfig).where(EasyConnectConfig.user_id == user.id)
            )
            existing = result.scalars().all()
            for config in existing:
                config.is_primary = False
        
        # Create webhook config
        webhook = EasyConnectConfig(
            user_id=user.id,
            alert_id=webhook_data.alert_id,
            webhook_secret=webhook_secret,
            name=webhook_data.name,
            description=webhook_data.description,
            tags=webhook_data.tags,
            webhook_priority=webhook_data.webhook_priority,
            is_primary=webhook_data.is_primary,
            routing_rule_id=UUID(webhook_data.routing_rule_id) if webhook_data.routing_rule_id else None
        )
        
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Created webhook for user {user.id}, name={webhook_data.name}")
        
        return WebhookResponse(
            id=str(webhook.id),
            name=webhook.name,
            description=webhook.description,
            alert_id=webhook.alert_id,
            webhook_url=f"{settings.BACKEND_URL}/webhook/qubic/events",
            tags=webhook.tags or [],
            webhook_priority=webhook.webhook_priority,
            is_primary=webhook.is_primary,
            routing_rule_id=str(webhook.routing_rule_id) if webhook.routing_rule_id else None,
            enabled=True,
            created_at=webhook.created_at,
            last_event_at=None,
            total_events=0
        )
        
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get webhook configuration details"""
    try:
        from app.config import settings
        
        query = select(EasyConnectConfig).where(
            and_(
                EasyConnectConfig.id == webhook_id,
                EasyConnectConfig.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return WebhookResponse(
            id=str(webhook.id),
            name=webhook.name,
            description=webhook.description,
            alert_id=webhook.alert_id,
            webhook_url=f"{settings.BACKEND_URL}/webhook/qubic/events",
            tags=webhook.tags or [],
            webhook_priority=webhook.webhook_priority,
            is_primary=webhook.is_primary,
            routing_rule_id=str(webhook.routing_rule_id) if webhook.routing_rule_id else None,
            enabled=getattr(webhook, 'enabled', True),
            created_at=webhook.created_at,
            last_event_at=None,
            total_events=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Update webhook configuration"""
    try:
        from app.config import settings
        
        query = select(EasyConnectConfig).where(
            and_(
                EasyConnectConfig.id == webhook_id,
                EasyConnectConfig.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Update fields
        update_data = webhook_data.dict(exclude_unset=True)
        
        # If setting as primary, unmark others
        if update_data.get('is_primary', False):
            result = await db.execute(
                select(EasyConnectConfig).where(
                    and_(
                        EasyConnectConfig.user_id == user.id,
                        EasyConnectConfig.id != webhook_id
                    )
                )
            )
            others = result.scalars().all()
            for other in others:
                other.is_primary = False
        
        for field, value in update_data.items():
            if field == 'routing_rule_id' and value:
                setattr(webhook, field, UUID(value))
            else:
                setattr(webhook, field, value)
        
        webhook.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Updated webhook {webhook_id}")
        
        return WebhookResponse(
            id=str(webhook.id),
            name=webhook.name,
            description=webhook.description,
            alert_id=webhook.alert_id,
            webhook_url=f"{settings.BACKEND_URL}/webhook/qubic/events",
            tags=webhook.tags or [],
            webhook_priority=webhook.webhook_priority,
            is_primary=webhook.is_primary,
            routing_rule_id=str(webhook.routing_rule_id) if webhook.routing_rule_id else None,
            enabled=getattr(webhook, 'enabled', True),
            created_at=webhook.created_at,
            last_event_at=None,
            total_events=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete webhook configuration"""
    try:
        query = select(EasyConnectConfig).where(
            and_(
                EasyConnectConfig.id == webhook_id,
                EasyConnectConfig.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        await db.delete(webhook)
        await db.commit()
        
        logger.info(f"Deleted webhook {webhook_id}")
        
        return {"status": "success", "message": "Webhook deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/list")
async def list_tags(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all unique tags used by user's webhooks"""
    try:
        query = select(EasyConnectConfig.tags).where(
            EasyConnectConfig.user_id == user.id
        )
        
        result = await db.execute(query)
        all_tags_lists = result.scalars().all()
        
        # Flatten and deduplicate
        tags = set()
        for tag_list in all_tags_lists:
            if tag_list:
                tags.update(tag_list)
        
        return {"tags": sorted(list(tags))}
        
    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=WebhookStats)
async def get_webhook_stats(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get webhook statistics"""
    try:
        # Get all webhooks
        query = select(EasyConnectConfig).where(
            EasyConnectConfig.user_id == user.id
        )
        
        result = await db.execute(query)
        webhooks = result.scalars().all()
        
        total_webhooks = len(webhooks)
        active_webhooks = sum(1 for w in webhooks if getattr(w, 'enabled', True))
        
        # Count events by tag (simplified)
        by_tag = {}
        for webhook in webhooks:
            if webhook.tags:
                for tag in webhook.tags:
                    by_tag[tag] = by_tag.get(tag, 0) + 1
        
        return WebhookStats(
            total_webhooks=total_webhooks,
            active_webhooks=active_webhooks,
            total_events=0,  # Would query events table
            events_today=0,  # Would query events table
            by_tag=by_tag
        )
        
    except Exception as e:
        logger.error(f"Error getting webhook stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{webhook_id}/regenerate-secret")
async def regenerate_webhook_secret(
    webhook_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate webhook secret (for security purposes)"""
    try:
        query = select(EasyConnectConfig).where(
            and_(
                EasyConnectConfig.id == webhook_id,
                EasyConnectConfig.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        webhook.webhook_secret = new_secret
        webhook.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Regenerated secret for webhook {webhook_id}")
        
        return {
            "status": "success",
            "message": "Webhook secret regenerated",
            "new_secret": new_secret
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating secret: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
