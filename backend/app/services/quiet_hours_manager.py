"""Quiet Hours Manager - Respect user's quiet hours for notifications"""
import logging
from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

from app.models.user import User

logger = logging.getLogger(__name__)


class QuietHoursManager:
    """
    Manage quiet hours for notifications
    
    Features:
    - Time zone support
    - Configurable quiet periods
    - Delayed delivery queue
    """
    
    def __init__(self):
        self.delayed_notifications = []
    
    def is_quiet_hours(
        self,
        user: User,
        check_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if current time is within user's quiet hours
        
        Args:
            user: User object with quiet hours config
            check_time: Time to check (defaults to now in user's timezone)
            
        Returns:
            True if in quiet hours, False otherwise
        """
        # Check if quiet hours enabled
        if not hasattr(user, 'quiet_hours_enabled') or not user.quiet_hours_enabled:
            return False
        
        # Get user's timezone (default to UTC if not set)
        tz_str = getattr(user, 'quiet_hours_timezone', 'UTC')
        try:
            tz = ZoneInfo(tz_str)
        except Exception:
            logger.warning(f"Invalid timezone {tz_str}, defaulting to UTC")
            tz = ZoneInfo('UTC')
        
        # Get current time in user's timezone
        if check_time is None:
            check_time = datetime.now(tz)
        else:
            check_time = check_time.astimezone(tz)
        
        current_time = check_time.time()
        
        # Get quiet hours config
        quiet_start = getattr(user, 'quiet_hours_start', time(22, 0))  # Default 10 PM
        quiet_end = getattr(user, 'quiet_hours_end', time(8, 0))  # Default 8 AM
        
        # Check if in quiet period
        if quiet_start < quiet_end:
            # Normal case: 22:00 - 08:00
            in_quiet = quiet_start <= current_time < quiet_end
        else:
            # Crosses midnight: e.g., 20:00 - 02:00
            in_quiet = current_time >= quiet_start or current_time < quiet_end
        
        if in_quiet:
            logger.info(
                f"User {user.id} is in quiet hours",
                current_time=current_time.isoformat(),
                quiet_start=quiet_start.isoformat(),
                quiet_end=quiet_end.isoformat()
            )
        
        return in_quiet
    
    def get_next_send_time(
        self,
        user: User,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """
        Get the next time notification can be sent (after quiet hours)
        
        Args:
            user: User object
            from_time: Starting time (defaults to now)
            
        Returns:
            Next datetime when notification can be sent
        """
        # Get user's timezone
        tz_str = getattr(user, 'quiet_hours_timezone', 'UTC')
        try:
            tz = ZoneInfo(tz_str)
        except Exception:
            tz = ZoneInfo('UTC')
        
        if from_time is None:
            from_time = datetime.now(tz)
        else:
            from_time = from_time.astimezone(tz)
        
        # If not in quiet hours, can send now
        if not self.is_quiet_hours(user, from_time):
            return from_time
        
        # Get quiet hours end time
        quiet_end = getattr(user, 'quiet_hours_end', time(8, 0))
        
        # Calculate next send time (end of quiet hours today or tomorrow)
        next_send = from_time.replace(
            hour=quiet_end.hour,
            minute=quiet_end.minute,
            second=0,
            microsecond=0
        )
        
        # If quiet_end already passed today, use tomorrow
        if next_send <= from_time:
            from datetime import timedelta
            next_send += timedelta(days=1)
        
        logger.info(
            f"Next send time for user {user.id}: {next_send.isoformat()}"
        )
        
        return next_send
    
    def should_send_now(
        self,
        user: User,
        severity: str
    ) -> bool:
        """
        Determine if notification should be sent now or delayed
        
        Critical alerts may override quiet hours
        
        Args:
            user: User object
            severity: Detection severity
            
        Returns:
            True if should send now, False if should delay
        """
        # Critical alerts always send (override quiet hours)
        if severity == 'CRITICAL':
            return True
        
        # High alerts might override based on user preference
        if severity == 'HIGH':
            override_high = getattr(user, 'quiet_hours_override_high', True)
            if override_high:
                return True
        
        # Check quiet hours
        if self.is_quiet_hours(user):
            logger.info(
                f"Delaying {severity} notification due to quiet hours",
                user_id=str(user.id)
            )
            return False
        
        return True
    
    def format_quiet_hours_message(self, user: User) -> str:
        """Get human-readable quiet hours configuration"""
        
        if not hasattr(user, 'quiet_hours_enabled') or not user.quiet_hours_enabled:
            return "Quiet hours disabled"
        
        quiet_start = getattr(user, 'quiet_hours_start', time(22, 0))
        quiet_end = getattr(user, 'quiet_hours_end', time(8, 0))
        tz_str = getattr(user, 'quiet_hours_timezone', 'UTC')
        
        return f"{quiet_start.strftime('%H:%M')} - {quiet_end.strftime('%H:%M')} ({tz_str})"


# Global instance
quiet_hours_manager = QuietHoursManager()
