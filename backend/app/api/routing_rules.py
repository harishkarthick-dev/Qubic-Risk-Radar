"""API endpoints for notification routing rules"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from pydantic import BaseModel

from app.database import get_db
from app.models.ai_detection import NotificationRoutingRule, NotificationLog
from app.models.user import User
from app.api.auth import get_verified_user
from app.services.notification_router import NotificationRouter
from app.logging_config import get_logger

router = APIRouter(prefix="/api/routing-rules", tags=["routing-rules"])
logger = get_logger(__name__)


# Pydantic models
class RoutingRuleCreate(BaseModel):
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    incident_type: Optional[str] = None
    scope: Optional[str] = None
    discord_channel_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: bool = False
    webhook_url: Optional[str] = None
    notification_format: str = 'minimal'  # minimal, standard, detailed
    include_ai_analysis: bool = True
    priority: int = 5
    enabled: bool = True


class RoutingRuleUpdate(BaseModel):
    incident_type: Optional[str] = None
    scope: Optional[str] = None
    discord_channel_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    notification_format: Optional[str] = None
    include_ai_analysis: Optional[bool] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class RoutingRuleResponse(BaseModel):
    id: str
    severity: str
    incident_type: Optional[str]
    scope: Optional[str]
    discord_channel_id: Optional[str]
    telegram_chat_id: Optional[str]
    email_enabled: bool
    webhook_url: Optional[str]
    notification_format: str
    include_ai_analysis: bool
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[RoutingRuleResponse])
async def list_routing_rules(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all routing rules for the authenticated user
    
    Returns rules sorted by severity and priority
    """
    try:
        query = (
            select(NotificationRoutingRule)
            .where(NotificationRoutingRule.user_id == user.id)
            .order_by(
                NotificationRoutingRule.priority.desc(),
                NotificationRoutingRule.created_at.desc()
            )
        )
        
        result = await db.execute(query)
        rules = result.scalars().all()
        
        return [RoutingRuleResponse.from_orm(rule) for rule in rules]
        
    except Exception as e:
        logger.error(f"Error listing routing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=RoutingRuleResponse)
async def create_routing_rule(
    rule_data: RoutingRuleCreate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new routing rule
    
    Rules determine how notifications are delivered based on severity
    """
    try:
        # Validate severity
        valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        if rule_data.severity not in valid_severities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity. Must be one of: {', '.join(valid_severities)}"
            )
        
        # Check if rule already exists for this severity (optional: allow multiple)
        existing = await db.execute(
            select(NotificationRoutingRule).where(
                and_(
                    NotificationRoutingRule.user_id == user.id,
                    NotificationRoutingRule.severity == rule_data.severity,
                    NotificationRoutingRule.incident_type == rule_data.incident_type,
                    NotificationRoutingRule.scope == rule_data.scope
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="A routing rule with these conditions already exists"
            )
        
        # Create rule
        rule = NotificationRoutingRule(
            user_id=user.id,
            **rule_data.dict()
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"Created routing rule for user {user.id}, severity={rule_data.severity}")
        
        return RoutingRuleResponse.from_orm(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating routing rule: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}", response_model=RoutingRuleResponse)
async def get_routing_rule(
    rule_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific routing rule"""
    try:
        query = select(NotificationRoutingRule).where(
            and_(
                NotificationRoutingRule.id == rule_id,
                NotificationRoutingRule.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Routing rule not found")
        
        return RoutingRuleResponse.from_orm(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting routing rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: UUID,
    rule_data: RoutingRuleUpdate,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing routing rule"""
    try:
        query = select(NotificationRoutingRule).where(
            and_(
                NotificationRoutingRule.id == rule_id,
                NotificationRoutingRule.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Routing rule not found")
        
        # Update fields
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        rule.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"Updated routing rule {rule_id}")
        
        return RoutingRuleResponse.from_orm(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating routing rule: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rule_id}")
async def delete_routing_rule(
    rule_id: UUID,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a routing rule"""
    try:
        query = select(NotificationRoutingRule).where(
            and_(
                NotificationRoutingRule.id == rule_id,
                NotificationRoutingRule.user_id == user.id
            )
        )
        
        result = await db.execute(query)
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Routing rule not found")
        
        await db.delete(rule)
        await db.commit()
        
        logger.info(f"Deleted routing rule {rule_id}")
        
        return {"status": "success", "message": "Routing rule deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting routing rule: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init-defaults")
async def initialize_default_rules(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize default routing rules for user
    
    Creates sensible defaults if user has no rules yet
    """
    try:
        # Check if user already has rules
        existing = await db.execute(
            select(NotificationRoutingRule).where(
                NotificationRoutingRule.user_id == user.id
            )
        )
        
        if existing.scalars().all():
            raise HTTPException(
                status_code=400,
                detail="User already has routing rules"
            )
        
        # Create default rules
        router_service = NotificationRouter(db)
        await router_service.create_default_rules(user.id)
        
        return {
            "status": "success",
            "message": "Default routing rules created"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing defaults: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Notification Logs endpoints
logs_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationLogResponse(BaseModel):
    id: str
    channel: str
    destination: str
    severity: Optional[str]
    status: str
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


@logs_router.get("/logs", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    limit: int = 50,
    offset: int = 0,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification delivery logs
    
    Query parameters:
    - limit: Max results (default 50, max 200)
    - offset: Pagination offset
    - channel: Filter by channel (discord, telegram, email, webhook)
    - status: Filter by status (sent, failed, pending)
    """
    try:
        # Build query
        conditions = [NotificationLog.user_id == user.id]
        
        if channel:
            conditions.append(NotificationLog.channel == channel)
        
        if status:
            conditions.append(NotificationLog.status == status)
        
        query = (
            select(NotificationLog)
            .where(and_(*conditions))
            .order_by(desc(NotificationLog.created_at))
            .limit(min(limit, 200))
            .offset(offset)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [NotificationLogResponse.from_orm(log) for log in logs]
        
    except Exception as e:
        logger.error(f"Error fetching notification logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@logs_router.get("/stats")
async def get_notification_stats(
    user: User = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification delivery statistics"""
    try:
        # Get all logs for user
        query = select(NotificationLog).where(NotificationLog.user_id == user.id)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Calculate stats
        total = len(logs)
        by_channel = {}
        by_status = {}
        
        for log in logs:
            by_channel[log.channel] = by_channel.get(log.channel, 0) + 1
            by_status[log.status] = by_status.get(log.status, 0) + 1
        
        success_rate = 0.0
        sent = by_status.get('sent', 0)
        if total > 0:
            success_rate = (sent / total) * 100
        
        return {
            'total_notifications': total,
            'by_channel': by_channel,
            'by_status': by_status,
            'success_rate': round(success_rate, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
