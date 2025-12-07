"""Discord bot service for sending notifications"""
import discord
from discord.ext import commands
from typing import Optional
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class DiscordBotService:
    """Service for sending notifications via Discord bot"""
    
    def __init__(self):
        self.bot_token = settings.DISCORD_BOT_TOKEN
        # Use Intents for bot permissions
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
    
    async def send_dm(self, user_id: str, message: str) -> bool:
        """
        Send a DM to a Discord user
        
        Args:
            user_id: Discord user ID
            message: Message to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user object
            user = await self.client.fetch_user(int(user_id))
            
            if not user:
                logger.warning("discord_user_not_found", user_id=user_id)
                return False
            
            # Send DM
            await user.send(message)
            logger.info("discord_dm_sent", user_id=user_id)
            return True
            
        except discord.Forbidden:
            logger.warning("discord_dm_forbidden", user_id=user_id)
            return False
        except discord.HTTPException as e:
            logger.error("discord_http_error", user_id=user_id, error=str(e))
            return False
        except ValueError:
            logger.error("discord_invalid_user_id", user_id=user_id)
            return False
        except Exception as e:
            logger.error("discord_send_error", user_id=user_id, error=str(e))
            return False
    
    async def send_welcome_message(self, user_id: str, full_name: str) -> bool:
        """Send welcome message to new user"""
        message = f"""🎉 **Welcome to Qubic Risk Radar, {full_name}!**

You'll receive instant alerts here when:
• Whale transfers detected
• Smart contract events triggered  
• Custom rules matched

Your Discord notifications are now active! ✅"""
        
        return await self.send_dm(user_id, message)
    
    async def send_incident_alert(self, user_id: str, incident_data: dict) -> bool:
        """Send incident alert notification"""
        severity_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        emoji = severity_emoji.get(incident_data.get("severity", "info"), "📊")
        
        message = f"""{emoji} **{incident_data.get('title', 'Alert')}**

**Severity:** {incident_data.get('severity', 'Unknown').upper()}
**Contract:** `{incident_data.get('contract_address', 'N/A')}`
**Details:** {incident_data.get('description', 'No description')}

View details: {settings.FRONTEND_URL}/incidents/{incident_data.get('id')}"""
        
        return await self.send_dm(user_id, message)
    
    async def connect(self):
        """Connect to Discord (call this on app startup)"""
        if not self.bot_token:
            logger.warning("discord_bot_token_not_configured")
            return
        
        try:
            await self.client.login(self.bot_token)
            logger.info("discord_bot_connected")
        except Exception as e:
            logger.error("discord_bot_connection_failed", error=str(e))
    
    async def close(self):
        """Close Discord connection"""
        await self.client.close()
        logger.info("discord_bot_disconnected")


# Global instance
discord_service = DiscordBotService()
