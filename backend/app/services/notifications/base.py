"""Base notification service with retry logic"""
from abc import ABC, abstractmethod
from typing import Optional
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.incident import Incident
from app.models.alert import Alert
from app.logging_config import get_logger
from app.config import settings

logger = get_logger(__name__)


class NotificationService(ABC):
    """Abstract base class for notification services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.max_retries = settings.NOTIFICATION_RETRY_MAX
        self.retry_delay = settings.NOTIFICATION_RETRY_DELAY
        self.timeout = settings.NOTIFICATION_TIMEOUT
    
    @abstractmethod
    async def send(self, incident: Incident) -> bool:
        """
        Send notification for incident
        
        Args:
            incident: Incident to notify about
            
        Returns:
            True if notification sent successfully
        """
        pass
    
    @abstractmethod
    def get_channel_name(self) -> str:
        """Get notification channel name (e.g., 'discord', 'telegram')"""
        pass
    
    @abstractmethod
    def get_target(self) -> str:
        """Get notification target (e.g., webhook URL, chat ID)"""
        pass
    
    async def send_with_retry(self, incident: Incident) -> bool:
        """
        Send notification with exponential backoff retry
        
        Args:
            incident: Incident to notify about
            
        Returns:
            True if notification sent successfully
        """
        alert = Alert(
            incident_id=incident.id,
            channel=self.get_channel_name(),
            target=self.get_target(),
            delivery_status='pending',
            payload_summary=f"{incident.severity}: {incident.title}"
        )
        self.db.add(alert)
        await self.db.commit()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "sending_notification",
                    channel=self.get_channel_name(),
                    incident_id=str(incident.id),
                    attempt=attempt + 1
                )
                
                success = await self.send(incident)
                
                if success:
                    alert.sent_at = datetime.utcnow()
                    alert.delivery_status = 'sent'
                    await self.db.commit()
                    
                    logger.info(
                        "notification_sent",
                        channel=self.get_channel_name(),
                        incident_id=str(incident.id)
                    )
                    return True
                
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    "notification_failed",
                    channel=self.get_channel_name(),
                    incident_id=str(incident.id),
                    attempt=attempt + 1,
                    error=error_msg
                )
                
                alert.error_message = error_msg
                alert.retry_count = attempt + 1
                
                if attempt < self.max_retries - 1:
                    alert.delivery_status = 'retried'
                    await self.db.commit()
                    
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    alert.delivery_status = 'failed'
                    await self.db.commit()
        
        return False
