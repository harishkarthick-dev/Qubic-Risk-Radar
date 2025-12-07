"""SendGrid email notification service"""
from typing import List, Dict, Any
import httpx
from app.models.incident import Incident
from app.services.notifications.base import NotificationService
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class EmailNotificationService(NotificationService):
    """Send notifications via SendGrid email API"""
    
    def get_channel_name(self) -> str:
        return "email"
    
    def get_target(self) -> str:
        return settings.ALERT_EMAIL_RECIPIENTS
    
    async def send(self, incident: Incident) -> bool:
        """Send email notification via SendGrid"""
        
        if not settings.SENDGRID_API_KEY or not settings.ALERT_EMAIL_RECIPIENTS:
            logger.warning("sendgrid_not_configured")
            return False
        
        # Build email payload
        payload = self._build_email_payload(incident)
        
        # Send via SendGrid API
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        
        return True
    
    def _build_email_payload(self, incident: Incident) -> Dict[str, Any]:
        """Build SendGrid email payload"""
        
        # Parse recipients
        recipients = [
            {"email": email.strip()}
            for email in settings.ALERT_EMAIL_RECIPIENTS.split(",")
            if email.strip()
        ]
        
        # Build HTML content
        html_content = self._build_html_template(incident)
        
        # Emoji for subject
        emoji = {
            'CRITICAL': '🚨',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
        }.get(incident.severity, 'ℹ️')
        
        payload = {
            "personalizations": [
                {
                    "to": recipients,
                    "subject": f"{emoji} {incident.severity} Alert - {incident.title}"
                }
            ],
            "from": {
                "email": settings.SENDGRID_FROM_EMAIL,
                "name": "Qubic Risk Radar"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        return payload
    
    def _build_html_template(self, incident: Incident) -> str:
        """Build HTML email template"""
        
        metadata = incident.metadata_json or {}
        
        # Severity colors
        colors = {
            'CRITICAL': '#f44336',  # Red
            'WARNING': '#ff9800',   # Orange
            'INFO': '#2196F3',      # Blue
        }
        bg_color = colors.get(incident.severity, colors['INFO'])
        
        # Build table rows
        rows = [
            f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Type</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{incident.type}</td></tr>",
            f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Severity</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{incident.severity}</td></tr>",
            f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Status</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{incident.status.upper()}</td></tr>",
        ]
        
        if incident.protocol:
            rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Protocol</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{incident.protocol}</td></tr>")
        
        if metadata.get('amount') and metadata.get('token'):
            rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Amount</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{metadata['amount']:,} {metadata['token']}</td></tr>")
        
        if incident.primary_wallet:
            rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Wallet</strong></td><td style='padding: 8px; border: 1px solid #ddd;'><code>{incident.primary_wallet}</code></td></tr>")
        
        if incident.contract_address:
            rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Contract</strong></td><td style='padding: 8px; border: 1px solid #ddd;'><code>{incident.contract_address}</code></td></tr>")
        
        if metadata.get('tx_hash'):
            tx_hash = metadata['tx_hash']
            explorer_link = f"https://explorer.qubic.org/network/tx/{tx_hash}"
            rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Transaction</strong></td><td style='padding: 8px; border: 1px solid #ddd;'><a href='{explorer_link}'>View on Explorer</a></td></tr>")
        
        rows.append(f"<tr><td style='padding: 8px; border: 1px solid #ddd;'><strong>Time</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{incident.first_seen_at.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>")
        
        table_rows = "\n".join(rows)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="background: {bg_color}; color: #ffffff; padding: 20px;">
            <h1 style="margin: 0; font-size: 24px;">{incident.severity} Alert</h1>
        </div>
        <div style="padding: 20px;">
            <h2 style="margin-top: 0; color: #333;">{incident.title}</h2>
            <p style="color: #666; line-height: 1.6;">{incident.description or ''}</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                {table_rows}
            </table>
            
            <a href="https://dashboard.qubicradar.io/incidents/{incident.id}" 
               style="display: inline-block; background: {bg_color}; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 20px;">
                View Full Incident Details
            </a>
        </div>
        <div style="padding: 20px; background: #f9f9f9; text-align: center; color: #999; font-size: 12px;">
            <p style="margin: 0;">Qubic Risk Radar - Blockchain Monitoring & Alerting</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
