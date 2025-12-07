"""Email service using Python's built-in smtplib"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    """Send emails using SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send HTML email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body
            text_content: Plain text fallback (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info("email_sent", to=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            return False
    
    def send_verification_email(self, to_email: str, full_name: str, verification_token: str) -> bool:
        """
        Send email verification email
        
        Args:
            to_email: User's email
            full_name: User's name
            verification_token: Verification token
            
        Returns:
            True if sent successfully
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #3b82f6; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Qubic Risk Radar!</h1>
        </div>
        <div class="content">
            <p>Hi {full_name},</p>
            <p>Thank you for signing up for Qubic Risk Radar. We're excited to have you on board!</p>
            <p>To complete your registration and start monitoring the Qubic blockchain, please verify your email address by clicking the button below:</p>
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #3b82f6;">{verification_url}</p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p>If you didn't create an account with Qubic Risk Radar, please ignore this email.</p>
            <p>Best regards,<br>The Qubic Risk Radar Team</p>
        </div>
        <div class="footer">
            <p>&copy; 2025 Qubic Risk Radar. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        text_content = f"""
Welcome to Qubic Risk Radar!

Hi {full_name},

Thank you for signing up! Please verify your email address by visiting:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Qubic Risk Radar Team
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Verify your Qubic Risk Radar account",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_welcome_email(self, to_email: str, full_name: str) -> bool:
        """
        Send welcome email after verification
        
        Args:
            to_email: User's email
            full_name: User's name
            
        Returns:
            True if sent successfully
        """
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .feature {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Email Verified!</h1>
        </div>
        <div class="content">
            <p>Hi {full_name},</p>
            <p>Your email has been successfully verified! You now have full access to Qubic Risk Radar.</p>
            
            <h2>🚀 Your Pro Plan {"Trial" if settings.PRICING_ENABLED else "Access"}</h2>
            <p>You've been automatically enrolled in our <strong>Pro Plan</strong>{" for <strong>30 days FREE</strong>!" if settings.PRICING_ENABLED else " with unlimited access!"}!</p>
            
            <div class="feature">
                <strong>✓ 200 EasyConnect alerts/month</strong>
            </div>
            <div class="feature">
                <strong>✓ 50 custom detection rules</strong>
            </div>
            <div class="feature">
                <strong>✓ Discord, Telegram & Email notifications</strong>
            </div>
            <div class="feature">
                <strong>✓ Whale activity tracking</strong>
            </div>
            <div class="feature">
                <strong>✓ Real-time monitoring dashboard</strong>
            </div>
            
            <p style="text-align: center;">
                <a href="{dashboard_url}" class="button">Go to Dashboard</a>
            </p>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Configure your EasyConnect alerts</li>
                <li>Create custom detection rules</li>
                <li>Set up notification channels</li>
                <li>Start monitoring the Qubic blockchain!</li>
            </ol>
            
            <p>If you have any questions, feel free to reply to this email.</p>
            <p>Best regards,<br>The Qubic Risk Radar Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Welcome to Qubic Risk Radar - Pro Trial Activated!",
            html_content=html_content
        )
    
    def send_onboarding_complete_email(self, to_email: str, full_name: str, user_data: dict) -> bool:
        """
        Send welcome email after onboarding completion
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            user_data: Dict with discord_verified, telegram_verified, email_enabled, plan_name, trial_end
        """
        subject = "🎉 Welcome to Qubic Risk Radar - You're All Set!"
        
        # Build active channels list
        channels = []
        if user_data.get('discord_verified'):
            channels.append('<span class="channel">💬 Discord</span>')
        if user_data.get('telegram_verified'):
            channels.append('<span class="channel">📱 Telegram</span>')
        if user_data.get('email_enabled'):
            channels.append('<span class="channel">📧 Email</span>')
        
        channels_html = ''.join(channels) if channels else '<span class="channel">📧 Email</span>'
        
        trial_info = ''
        if user_data.get('trial_end'):
            trial_info = f"(Trial until {user_data['trial_end']})"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
    .content {{ background: #f9fafb; padding: 30px; }}
    .setup-summary {{ background: white; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; }}
    .channel {{ display: inline-block; background: #e0e7ff; color: #4c51bf; padding: 5px 12px; border-radius: 15px; margin: 5px; }}
    .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
    .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
    .tip {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🚀 You're Ready to Go!</h1>
      <p>Your Qubic Risk Radar is now fully configured</p>
    </div>
    
    <div class="content">
      <p>Hi <strong>{full_name}</strong>,</p>
      
      <p>Congratulations! You've successfully set up your account and you're now ready to monitor the Qubic blockchain like a pro.</p>
      
      <div class="setup-summary">
        <h3>✅ Your Setup Summary</h3>
        <p><strong>Webhook URL:</strong> Configured and tested ✓</p>
        <p><strong>Active Channels:</strong><br>
          {channels_html}
        </p>
        <p><strong>Plan:</strong> {user_data.get('plan_name', 'Pro')} {trial_info}</p>
      </div>
      
      <p>You're all set to receive real-time alerts whenever your monitored events are triggered. Your notifications will be delivered to all active channels above.</p>
      
      <div style="text-align: center; margin: 30px 0;">
        <a href="{settings.FRONTEND_URL}/dashboard" class="btn">Go to Dashboard</a>
      </div>
      
      <div class="tip">
        <strong>💡 Pro Tip:</strong> You can add more alerts or update your notification preferences anytime from the Settings page.
      </div>
      
      <p>Need help? Check out our <a href="{settings.FRONTEND_URL}/docs">documentation</a> or reach out to support.</p>
      
      <p>Happy monitoring!<br>
      <strong>The Qubic Risk Radar Team</strong></p>
    </div>
    
    <div class="footer">
      <p>Qubic Risk Radar - Real-time blockchain monitoring and alerting</p>
      <p><a href="{settings.FRONTEND_URL}/settings">Manage Preferences</a></p>
    </div>
  </div>
</body>
</html>
        """
        
        text_content = f"""
Welcome to Qubic Risk Radar!

Hi {full_name},

Your account is now fully configured and ready to monitor the Qubic blockchain.

Active Channels: {', '.join([c for c in ['Discord' if user_data.get('discord_verified') else '', 'Telegram' if user_data.get('telegram_verified') else '', 'Email' if user_data.get('email_enabled') else ''] if c])}
Plan: {user_data.get('plan_name', 'Pro')} {trial_info}

Visit your dashboard: {settings.FRONTEND_URL}/dashboard

Happy monitoring!
The Qubic Risk Radar Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
