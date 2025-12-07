"""Telegram Bot API notification service"""
from typing import Dict, Any
import httpx
from app.models.incident import Incident
from app.services.notifications.base import NotificationService
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class TelegramNotificationService(NotificationService):
    """Send notifications to Telegram via Bot API"""
    
    def get_channel_name(self) -> str:
        return "telegram"
    
    def get_target(self) -> str:
        return settings.TELEGRAM_CHAT_ID
    
    async def send(self, incident: Incident) -> bool:
        """Send Telegram notification with HTML formatting"""
        
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.warning("telegram_not_configured")
            return False
        
        # Build message
        message = self._build_message(incident)
        
        # Send via Bot API
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        
        return True
    
    def _build_message(self, incident: Incident) -> str:
        """Build HTML-formatted Telegram message"""
        
        # Emoji based on severity
        emoji = {
            'CRITICAL': '🚨',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
        }.get(incident.severity, 'ℹ️')
        
        metadata = incident.metadata_json or {}
        
        # Build message parts
        parts = [
            f"{emoji} <b>{incident.severity} Alert</b>\n",
            f"<b>{incident.title}</b>\n",
        ]
        
        if incident.description:
            parts.append(f"{incident.description}\n")
        
        parts.append("")  # Blank line
        
        # Add details
        parts.append(f"<b>Type:</b> {incident.type}")
        
        if incident.protocol:
            parts.append(f"<b>Protocol:</b> {incident.protocol}")
        
        if metadata.get('amount') and metadata.get('token'):
            parts.append(f"<b>Amount:</b> {metadata['amount']:,} {metadata['token']}")
        
        if incident.primary_wallet:
            wallet = incident.primary_wallet
            wallet_display = f"{wallet[:12]}...{wallet[-8:]}" if len(wallet) > 24 else wallet
            parts.append(f"<b>Wallet:</b> <code>{wallet_display}</code>")
        
        if incident.contract_address:
            contract = incident.contract_address
            contract_display = f"{contract[:12]}...{contract[-8:]}" if len(contract) > 24 else contract
            parts.append(f"<b>Contract:</b> <code>{contract_display}</code>")
        
        if metadata.get('tx_hash'):
            tx_hash = metadata['tx_hash']
            tx_display = f"{tx_hash[:12]}...{tx_hash[-8:]}" if len(tx_hash) > 24 else tx_hash
            parts.append(f"<b>Transaction:</b> <code>{tx_display}</code>")
        
        parts.append(f"<b>Time:</b> {incident.first_seen_at.strftime('%Y-%m-%d %H:%M UTC')}")
        parts.append(f"<b>Status:</b> {incident.status.upper()}")
        
        # Add dashboard link (assuming frontend deployed)
        parts.append("")
        parts.append(f'<a href="https://dashboard.qubicradar.io/incidents/{incident.id}">View Details</a>')
        
        return "\n".join(parts)
