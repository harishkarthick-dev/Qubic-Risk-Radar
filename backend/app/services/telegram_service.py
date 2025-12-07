"""Telegram bot service for sending notifications"""
import httpx
from typing import Optional
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class TelegramBotService:
    """Service for sending notifications via Telegram bot"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to a Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            message: Message to send
            parse_mode: Message formatting (HTML or Markdown)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            logger.warning("telegram_bot_token_not_configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": parse_mode
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("telegram_message_sent", chat_id=chat_id)
                    return True
                else:
                    logger.warning(
                        "telegram_send_failed",
                        chat_id=chat_id,
                        status_code=response.status_code,
                        response=response.text
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error("telegram_timeout", chat_id=chat_id)
            return False
        except Exception as e:
            logger.error("telegram_send_error", chat_id=chat_id, error=str(e))
            return False
    
    async def send_welcome_message(self, chat_id: str, full_name: str) -> bool:
        """Send welcome message to new user"""
        message = f"""🚀 <b>Qubic Risk Radar Connected!</b>

Hi {full_name},

You're all set to receive real-time blockchain alerts.

You'll be notified here when:
• Whale transfers detected
• Smart contract events triggered
• Custom rules matched

Your Telegram notifications are now active! ✅"""
        
        return await self.send_message(chat_id, message)
    
    async def send_incident_alert(self, chat_id: str, incident_data: dict) -> bool:
        """Send incident alert notification"""
        severity_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        emoji = severity_emoji.get(incident_data.get("severity", "info"), "📊")
        
        message = f"""{emoji} <b>{incident_data.get('title', 'Alert')}</b>

<b>Severity:</b> {incident_data.get('severity', 'Unknown').upper()}
<b>Contract:</b> <code>{incident_data.get('contract_address', 'N/A')}</code>
<b>Details:</b> {incident_data.get('description', 'No description')}

<a href="{settings.FRONTEND_URL}/incidents/{incident_data.get('id')}">View Details</a>"""
        
        return await self.send_message(chat_id, message)


# Global instance
telegram_service = TelegramBotService()
