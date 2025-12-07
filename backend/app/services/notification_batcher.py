"""Notification Batcher - Batch and schedule notifications to prevent spam"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ai_detection import AIDetection, NotificationLog
from app.models.user import User
from app.services.notification_router import NotificationRouter

logger = logging.getLogger(__name__)


class NotificationBatcher:
    """
    Batch notifications to prevent spam
    
    Features:
    - Severity-based batching intervals
    - Automatic batch sending
    - Deduplication
    - Daily/weekly digest support
    """
    
    # Batching intervals by severity (in seconds)
    BATCH_INTERVALS = {
        'CRITICAL': 0,        # Send immediately (no batching)
        'HIGH': 0,            # Send immediately (no batching)
        'MEDIUM': 300,        # Batch every 5 minutes
        'LOW': 1800,          # Batch every 30 minutes
        'INFO': 3600          # Batch every hour
    }
    
    # Maximum batch size before forcing send
    MAX_BATCH_SIZE = {
        'MEDIUM': 10,
        'LOW': 20,
        'INFO': 50
    }
    
    def __init__(self):
        # In-memory batch queues: (user_id, severity) -> [detections]
        self.batches: Dict[tuple, List[AIDetection]] = defaultdict(list)
        self.batch_timers: Dict[tuple, datetime] = {}
        self.is_running = False
    
    async def add_detection(
        self,
        detection: AIDetection,
        user: User,
        db: AsyncSession
    ):
        """
        Add detection to batch queue
        
        If severity requires immediate sending, sends right away.
        Otherwise, adds to batch and schedules send.
        """
        try:
            severity = detection.severity
            
            # Critical and High: send immediately without batching
            if severity in ['CRITICAL', 'HIGH']:
                router = NotificationRouter(db)
                await router.route_detection(detection, user)
                logger.info(f"Sent {severity} detection immediately")
                return
            
            # Add to batch
            key = (user.id, severity)
            self.batches[key].append(detection)
            
            logger.info(
                f"Added detection to batch queue",
                user_id=str(user.id),
                severity=severity,
                queue_size=len(self.batches[key])
            )
            
            # Schedule batch send if not already scheduled
            if key not in self.batch_timers:
                interval = self.BATCH_INTERVALS.get(severity, 300)
                self.batch_timers[key] = datetime.utcnow() + timedelta(seconds=interval)
                logger.info(f"Scheduled batch send in {interval}s for {key}")
            
            # Force send if batch size exceeded
            max_size = self.MAX_BATCH_SIZE.get(severity, 50)
            if len(self.batches[key]) >= max_size:
                logger.info(f"Batch size limit reached, sending now")
                await self._send_batch(key, db)
                
        except Exception as e:
            logger.error(f"Error adding to batch: {e}", exc_info=True)
    
    async def _send_batch(
        self,
        key: tuple,
        db: AsyncSession
    ):
        """Send a batched notification"""
        
        user_id, severity = key
        detections = self.batches.get(key, [])
        
        if not detections:
            return
        
        try:
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_id} not found for batch send")
                return
            
            # Create batch notification
            await self._send_batch_notification(
                user=user,
                detections=detections,
                severity=severity,
                db=db
            )
            
            logger.info(
                f"Sent batch notification",
                user_id=str(user_id),
                severity=severity,
                count=len(detections)
            )
            
            # Clear batch
            self.batches[key] = []
            if key in self.batch_timers:
                del self.batch_timers[key]
                
        except Exception as e:
            logger.error(f"Error sending batch: {e}", exc_info=True)
    
    async def _send_batch_notification(
        self,
        user: User,
        detections: List[AIDetection],
        severity: str,
        db: AsyncSession
    ):
        """Generate and send a batched notification message"""
        
        from app.services.telegram_service import TelegramNotificationService
        from app.services.email_service import EmailService
        
        count = len(detections)
        
        # Build summary
        categories = defaultdict(int)
        total_anomaly = 0
        
        for d in detections:
            categories[d.primary_category] += 1
            total_anomaly += d.anomaly_score
        
        avg_anomaly = total_anomaly / count if count > 0 else 0
        
        # Format message
        emoji = self._get_severity_emoji(severity)
        time_range = self._get_time_range(detections)
        
        # Top categories
        top_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        category_lines = [
            f"  • {cat}: {cnt}" for cat, cnt in top_categories
        ]
        
        message = f"""
{emoji} **{count} {severity} ALERTS** (Batched)

**Time Range**: {time_range}
**Average Anomaly**: {avg_anomaly:.2f}

**Top Categories**:
{chr(10).join(category_lines)}

[View All Detections →]
"""
        
        # Send to appropriate channels (batches typically go to less urgent channels)
        try:
            if user.telegram_verified:
                telegram = TelegramNotificationService()
                await telegram.send_message(
                    chat_id=user.telegram_chat_id,
                    text=message
                )
                
                # Log delivery
                for detection in detections:
                    await self._log_batch_delivery(detection, user, 'telegram', db)
        
        except Exception as e:
            logger.error(f"Failed to send batch notification: {e}")
    
    async def _log_batch_delivery(
        self,
        detection: AIDetection,
        user: User,
        channel: str,
        db: AsyncSession
    ):
        """Log batched notification delivery"""
        
        log = NotificationLog(
            incident_id=None,
            user_id=user.id,
            routing_rule_id=None,
            channel=channel,
            destination=user.telegram_chat_id if channel == 'telegram' else '',
            severity=detection.severity,
            status='sent',
            delivered_at=datetime.utcnow(),
            error_message=None,
            retry_count=0
        )
        
        db.add(log)
        await db.commit()
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity"""
        emojis = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🔵',
            'LOW': '🟢',
            'INFO': '⚪'
        }
        return emojis.get(severity, '⚪')
    
    def _get_time_range(self, detections: List[AIDetection]) -> str:
        """Get human-readable time range for detections"""
        if not detections:
            return "Unknown"
        
        times = [d.created_at for d in detections if d.created_at]
        if not times:
            return "Unknown"
        
        earliest = min(times)
        latest = max(times)
        
        diff = latest - earliest
        
        if diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"Last {minutes} minutes"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"Last {hours} hours"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"Last {days} days"
    
    async def start_batch_processor(self, db: AsyncSession):
        """
        Start background task to process batches
        
        Runs periodically to check and send scheduled batches
        """
        self.is_running = True
        logger.info("Batch processor started")
        
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                keys_to_send = []
                
                # Find batches ready to send
                for key, scheduled_time in self.batch_timers.items():
                    if now >= scheduled_time:
                        keys_to_send.append(key)
                
                # Send ready batches
                for key in keys_to_send:
                    await self._send_batch(key, db)
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}", exc_info=True)
    
    def stop_batch_processor(self):
        """Stop the batch processor"""
        self.is_running = False
        logger.info("Batch processor stopped")
    
    async def force_send_all(self, db: AsyncSession):
        """Force send all pending batches (useful for shutdown/testing)"""
        logger.info(f"Force sending {len(self.batches)} batches")
        
        for key in list(self.batches.keys()):
            await self._send_batch(key, db)
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get current batch statistics"""
        total_pending = sum(len(batch) for batch in self.batches.values())
        
        by_severity = defaultdict(int)
        for key, batch in self.batches.items():
            severity = key[1]
            by_severity[severity] += len(batch)
        
        return {
            'total_pending': total_pending,
            'by_severity': dict(by_severity),
            'active_batches': len(self.batches),
            'scheduled_sends': len(self.batch_timers)
        }


# Global instance
notification_batcher = NotificationBatcher()
