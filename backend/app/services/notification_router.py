"""Notification Router - Smart routing based on severity and user rules"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.ai_detection import AIDetection, NotificationRoutingRule, NotificationLog
from app.models.user import User
from app.services.discord_service import DiscordNotificationService
from app.services.telegram_service import TelegramNotificationService
from app.services.email_service import EmailService
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationRouter:
    """
    Smart notification routing system
    
    Routes notifications based on:
    - Severity level
    - User-defined routing rules
    - Channel availability
    - Quiet hours (if configured)
    """
    
    # Default routing configuration (used if no rules defined)
    DEFAULT_ROUTING = {
        'CRITICAL': ['discord', 'telegram', 'email'],
        'HIGH': ['discord', 'telegram'],
        'MEDIUM': ['telegram'],
        'LOW': [],  # Batched only
        'INFO': []  # Batched only
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.discord_service = DiscordNotificationService()
        self.telegram_service = TelegramNotificationService()
        self.email_service = EmailService()
    
    async def route_detection(
        self,
        detection: AIDetection,
        user: User
    ) -> Dict[str, Any]:
        """
        Route detection notification based on configured rules
        
        Returns:
            Dict with delivery results by channel
        """
        try:
            # Get routing rules for this detection
            rules = await self._get_matching_rules(detection, user.id)
            
            if not rules:
                # Use default routing
                logger.info(f"No custom rules found for user {user.id}, using defaults")
                return await self._route_with_defaults(detection, user)
            
            # Execute matching rules
            results = {}
            for rule in rules:
                if not rule.enabled:
                    continue
                
                channel_results = await self._execute_routing_rule(rule, detection, user)
                results.update(channel_results)
            
            logger.info(
                f"Routed detection {detection.id} to {len(results)} channels",
                detection_id=str(detection.id),
                channels=list(results.keys())
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Routing error: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    async def _get_matching_rules(
        self,
        detection: AIDetection,
        user_id: UUID
    ) -> List[NotificationRoutingRule]:
        """Get all routing rules that match this detection"""
        
        # Build query conditions
        conditions = [
            NotificationRoutingRule.user_id == user_id,
            NotificationRoutingRule.enabled == True
        ]
        
        # Match severity
        conditions.append(NotificationRoutingRule.severity == detection.severity)
        
        # Optional: match incident type (category)
        # Rules with NULL incident_type match all categories
        
        query = (
            select(NotificationRoutingRule)
            .where(and_(*conditions))
            .order_by(NotificationRoutingRule.priority.desc())
        )
        
        result = await self.db.execute(query)
        rules = result.scalars().all()
        
        return list(rules)
    
    async def _execute_routing_rule(
        self,
        rule: NotificationRoutingRule,
        detection: AIDetection,
        user: User
    ) -> Dict[str, bool]:
        """
        Execute a single routing rule
        
        Returns dict of channel -> delivery_success
        """
        results = {}
        
        # Discord
        if rule.discord_channel_id and user.discord_verified:
            try:
                await self.discord_service.send_detection_notification(
                    user_id=user.discord_user_id,
                    channel_id=rule.discord_channel_id,
                    detection=detection,
                    format=rule.notification_format
                )
                results['discord'] = True
                await self._log_delivery(detection, user, 'discord', 'sent')
            except Exception as e:
                logger.error(f"Discord delivery failed: {e}")
                results['discord'] = False
                await self._log_delivery(detection, user, 'discord', 'failed', str(e))
        
        # Telegram
        if rule.telegram_chat_id and user.telegram_verified:
            try:
                await self.telegram_service.send_detection_notification(
                    chat_id=rule.telegram_chat_id,
                    detection=detection,
                    format=rule.notification_format
                )
                results['telegram'] = True
                await self._log_delivery(detection, user, 'telegram', 'sent')
            except Exception as e:
                logger.error(f"Telegram delivery failed: {e}")
                results['telegram'] = False
                await self._log_delivery(detection, user, 'telegram', 'failed', str(e))
        
        # Email
        if rule.email_enabled and user.email:
            try:
                await self.email_service.send_detection_alert(
                    to_email=user.email,
                    detection=detection,
                    user=user
                )
                results['email'] = True
                await self._log_delivery(detection, user, 'email', 'sent')
            except Exception as e:
                logger.error(f"Email delivery failed: {e}")
                results['email'] = False
                await self._log_delivery(detection, user, 'email', 'failed', str(e))
        
        # Custom Webhook
        if rule.webhook_url:
            try:
                await self._send_webhook_notification(
                    url=rule.webhook_url,
                    detection=detection
                )
                results['webhook'] = True
                await self._log_delivery(detection, user, 'webhook', 'sent')
            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                results['webhook'] = False
                await self._log_delivery(detection, user, 'webhook', 'failed', str(e))
        
        return results
    
    async def _route_with_defaults(
        self,
        detection: AIDetection,
        user: User
    ) -> Dict[str, bool]:
        """Route using default configuration"""
        
        channels = self.DEFAULT_ROUTING.get(detection.severity, [])
        results = {}
        
        for channel in channels:
            if channel == 'discord' and user.discord_verified:
                try:
                    await self.discord_service.send_detection_notification(
                        user_id=user.discord_user_id,
                        channel_id=None,  # Default channel
                        detection=detection,
                        format='minimal'
                    )
                    results['discord'] = True
                    await self._log_delivery(detection, user, 'discord', 'sent')
                except Exception as e:
                    logger.error(f"Discord delivery failed: {e}")
                    results['discord'] = False
            
            elif channel == 'telegram' and user.telegram_verified:
                try:
                    await self.telegram_service.send_detection_notification(
                        chat_id=user.telegram_chat_id,
                        detection=detection,
                        format='minimal'
                    )
                    results['telegram'] = True
                    await self._log_delivery(detection, user, 'telegram', 'sent')
                except Exception as e:
                    logger.error(f"Telegram delivery failed: {e}")
                    results['telegram'] = False
            
            elif channel == 'email' and user.email:
                try:
                    await self.email_service.send_detection_alert(
                        to_email=user.email,
                        detection=detection,
                        user=user
                    )
                    results['email'] = True
                    await self._log_delivery(detection, user, 'email', 'sent')
                except Exception as e:
                    logger.error(f"Email delivery failed: {e}")
                    results['email'] = False
        
        return results
    
    async def _send_webhook_notification(
        self,
        url: str,
        detection: AIDetection
    ):
        """Send notification to custom webhook"""
        import httpx
        
        payload = {
            'detection_id': str(detection.id),
            'severity': detection.severity,
            'category': detection.primary_category,
            'anomaly_score': detection.anomaly_score,
            'confidence': detection.confidence,
            'summary': detection.summary,
            'timestamp': detection.created_at.isoformat()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    
    async def _log_delivery(
        self,
        detection: AIDetection,
        user: User,
        channel: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log notification delivery attempt"""
        
        log = NotificationLog(
            incident_id=None,  # Link to incident if exists
            user_id=user.id,
            routing_rule_id=None,
            channel=channel,
            destination=self._get_destination(user, channel),
            severity=detection.severity,
            status=status,
            delivered_at=datetime.utcnow() if status == 'sent' else None,
            error_message=error_message,
            retry_count=0
        )
        
        self.db.add(log)
        await self.db.commit()
    
    def _get_destination(self, user: User, channel: str) -> str:
        """Get destination address for channel"""
        if channel == 'discord':
            return user.discord_user_id or 'unknown'
        elif channel == 'telegram':
            return user.telegram_chat_id or 'unknown'
        elif channel == 'email':
            return user.email or 'unknown'
        elif channel == 'webhook':
            return 'custom_webhook'
        return 'unknown'
    
    async def create_default_rules(self, user_id: UUID):
        """Create default routing rules for a new user"""
        
        default_rules = [
            {
                'severity': 'CRITICAL',
                'discord_channel_id': None,
                'telegram_chat_id': None,
                'email_enabled': True,
                'notification_format': 'minimal',
                'priority': 10
            },
            {
                'severity': 'HIGH',
                'discord_channel_id': None,
                'telegram_chat_id': None,
                'email_enabled': False,
                'notification_format': 'minimal',
                'priority': 7
            },
            {
                'severity': 'MEDIUM',
                'discord_channel_id': None,
                'telegram_chat_id': None,
                'email_enabled': False,
                'notification_format': 'minimal',
                'priority': 5
            }
        ]
        
        for rule_data in default_rules:
            rule = NotificationRoutingRule(
                user_id=user_id,
                **rule_data
            )
            self.db.add(rule)
        
        await self.db.commit()
        logger.info(f"Created default routing rules for user {user_id}")
