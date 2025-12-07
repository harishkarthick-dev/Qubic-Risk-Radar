"""Discord webhook notification service"""
from typing import Dict, Any
import httpx
from app.models.incident import Incident
from app.services.notifications.base import NotificationService
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class DiscordNotificationService(NotificationService):
    """Send notifications to Discord via webhooks"""
    
    def get_channel_name(self) -> str:
        return "discord"
    
    def get_target(self) -> str:
        # Select webhook URL based on severity
        if hasattr(self, '_webhook_url'):
            return self._webhook_url
        
        severity_map = {
            'CRITICAL': settings.DISCORD_WEBHOOK_URL_CRITICAL,
            'WARNING': settings.DISCORD_WEBHOOK_URL_WARNING,
            'INFO': settings.DISCORD_WEBHOOK_URL_INFO,
        }
        
        url = severity_map.get(self.incident_severity, settings.DISCORD_WEBHOOK_URL_WARNING)
        self._webhook_url = url
        return url
    
    async def send(self, incident: Incident) -> bool:
        """Send Discord notification with rich embed"""
        self.incident_severity = incident.severity
        
        webhook_url = self.get_target()
        if not webhook_url:
            logger.warning("discord_webhook_not_configured", severity=incident.severity)
            return False
        
        # Build rich embed
        embed = self._build_embed(incident)
        payload = {
            "content": f"{'🚨' if incident.severity == 'CRITICAL' else '⚠️' if incident.severity == 'WARNING' else 'ℹ️'} **{incident.severity} Alert**",
            "embeds": [embed]
        }
        
        # Send webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        
        return True
    
    def _build_embed(self, incident: Incident) -> Dict[str, Any]:
        """Build Discord embed payload"""
        
        # Severity colors (decimal)
        colors = {
            'CRITICAL': 15158332,  # Red
            'WARNING': 16776960,   # Yellow
            'INFO': 3447003,       # Blue
        }
        
        metadata = incident.metadata_json or {}
        
        # Build fields
        fields = [
            {
                "name": "Severity",
                "value": incident.severity,
                "inline": True
            },
            {
                "name": "Type",
                "value": incident.type,
                "inline": True
            },
            {
                "name": "Status",
                "value": incident.status.upper(),
                "inline": True
            },
        ]
        
        if incident.protocol:
            fields.append({
                "name": "Protocol",
                "value": incident.protocol,
                "inline": True
            })
        
        if metadata.get('amount') and metadata.get('token'):
            fields.append({
                "name": "Amount",
                "value": f"{metadata['amount']:,} {metadata['token']}",
                "inline": True
            })
        
        if incident.primary_wallet:
            fields.append({
                "name": "Wallet",
                "value": f"`{incident.primary_wallet[:16]}...{incident.primary_wallet[-8:]}`" if len(incident.primary_wallet) > 24 else f"`{incident.primary_wallet}`",
                "inline": False
            })
        
        if incident.contract_address:
            fields.append({
                "name": "Contract",
                "value": f"`{incident.contract_address[:16]}...{incident.contract_address[-8:]}`" if len(incident.contract_address) > 24 else f"`{incident.contract_address}`",
                "inline": False
            })
        
        if metadata.get('tx_hash'):
            # Link to Qubic explorer (assuming explorer exists)
            tx_hash = metadata['tx_hash']
            explorer_link = f"https://explorer.qubic.org/network/tx/{tx_hash}"
            fields.append({
                "name": "Transaction",
                "value": f"[View on Explorer]({explorer_link})",
                "inline": False
            })
        
        embed = {
            "title": incident.title,
            "description": incident.description,
            "color": colors.get(incident.severity, colors['INFO']),
            "fields": fields,
            "footer": {
                "text": "Qubic Risk Radar"
            },
            "timestamp": incident.first_seen_at.isoformat()
        }
        
        return embed
