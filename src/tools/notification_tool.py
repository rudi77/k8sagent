"""
Notification tools for sending alerts through various channels (Slack, Teams, Email).
"""

import smtplib
from email.mime.text import MIMEText
from typing import List, Optional

import pymsteams
from slack_sdk.webhook import WebhookClient
from smolagents import tool

from src.config.settings import settings
from src.utils.logging import logger


class NotificationClient:
    """Helper class for sending notifications through various channels."""
    
    def __init__(self, channels: Optional[List[str]] = None):
        """
        Initialize the notification client.
        
        Args:
            channels: List of notification channels to enable
        """
        self.channels = channels or settings.notification_channels
        
        # Initialize Slack
        if "slack" in self.channels and settings.slack_webhook_url:
            self.slack_client = WebhookClient(settings.slack_webhook_url)
        else:
            self.slack_client = None
        
        # Initialize Teams
        if "teams" in self.channels and settings.teams_webhook_url:
            self.teams_client = pymsteams.connectorcard(settings.teams_webhook_url)
        else:
            self.teams_client = None
        
        # Initialize Email
        self.smtp_config = None
        if "email" in self.channels and all([
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_username,
            settings.smtp_password,
            settings.notification_email
        ]):
            self.smtp_config = {
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "username": settings.smtp_username,
                "password": settings.smtp_password,
                "from_email": settings.notification_email
            }
    
    def send_slack_notification(
        self,
        message: str,
        title: Optional[str] = None,
        severity: str = "info"
    ) -> bool:
        """
        Send a notification through Slack.
        
        Args:
            message: The message to send
            title: Optional title for the message
            severity: Severity level (info, warning, error)
            
        Returns:
            bool: Whether the notification was sent successfully
        """
        if not self.slack_client:
            logger.warning("Slack notifications not configured")
            return False
        
        try:
            # Set color based on severity
            color = {
                "info": "#36a64f",
                "warning": "#ffd700",
                "error": "#ff0000"
            }.get(severity.lower(), "#36a64f")
            
            blocks = []
            if title:
                blocks.append({
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                })
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            })
            
            response = self.slack_client.send(
                text=message,
                blocks=blocks,
                attachments=[{"color": color}]
            )
            
            if response.status_code == 200:
                logger.info("Successfully sent Slack notification")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def send_teams_notification(
        self,
        message: str,
        title: Optional[str] = None,
        severity: str = "info"
    ) -> bool:
        """
        Send a notification through Microsoft Teams.
        
        Args:
            message: The message to send
            title: Optional title for the message
            severity: Severity level (info, warning, error)
            
        Returns:
            bool: Whether the notification was sent successfully
        """
        if not self.teams_client:
            logger.warning("Teams notifications not configured")
            return False
        
        try:
            # Create a new teams message card
            teams_message = pymsteams.connectorcard(settings.teams_webhook_url)
            
            if title:
                teams_message.title(title)
            
            teams_message.text(message)
            
            # Add color based on severity
            if severity.lower() == "error":
                teams_message.color("#ff0000")
            elif severity.lower() == "warning":
                teams_message.color("#ffd700")
            
            teams_message.send()
            logger.info("Successfully sent Teams notification")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")
            return False
    
    def send_email_notification(
        self,
        message: str,
        subject: str,
        to_email: Optional[str] = None,
        severity: str = "info"
    ) -> bool:
        """
        Send a notification through email.
        
        Args:
            message: The message to send
            subject: Email subject
            to_email: Recipient email address
            severity: Severity level (info, warning, error)
            
        Returns:
            bool: Whether the notification was sent successfully
        """
        if not self.smtp_config:
            logger.warning("Email notifications not configured")
            return False
        
        try:
            # Create message
            msg = MIMEText(message)
            msg['Subject'] = f"[{severity.upper()}] {subject}"
            msg['From'] = self.smtp_config["from_email"]
            msg['To'] = to_email or self.smtp_config["from_email"]
            
            # Send email
            with smtplib.SMTP(
                self.smtp_config["host"],
                self.smtp_config["port"]
            ) as server:
                server.starttls()
                server.login(
                    self.smtp_config["username"],
                    self.smtp_config["password"]
                )
                server.send_message(msg)
            
            logger.info("Successfully sent email notification")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def notify(
        self,
        message: str,
        title: Optional[str] = None,
        severity: str = "info",
        channels: Optional[List[str]] = None
    ) -> dict:
        """
        Send a notification through all configured channels.
        
        Args:
            message: The message to send
            title: Optional title for the message
            severity: Severity level (info, warning, error)
            channels: Specific channels to use (defaults to all configured channels)
            
        Returns:
            dict: Status of notifications for each channel
        """
        channels = channels or self.channels
        results = {}
        
        if "slack" in channels:
            results["slack"] = self.send_slack_notification(
                message=message,
                title=title,
                severity=severity
            )
        
        if "teams" in channels:
            results["teams"] = self.send_teams_notification(
                message=message,
                title=title,
                severity=severity
            )
        
        if "email" in channels:
            results["email"] = self.send_email_notification(
                message=message,
                subject=title or "Kubernetes Monitor Alert",
                severity=severity
            )
        
        return results


# Create a global notification client
notification_client = NotificationClient()


# SmolAgents notification tools
@tool
def send_notification(
    message: str,
    title: Optional[str] = None,
    severity: str = "info"
) -> str:
    """
    Send a notification through all configured channels.
    
    Args:
        message: The message to send
        title: Optional title for the message
        severity: Severity level (info, warning, error)
    """
    results = notification_client.notify(message, title, severity)
    success_channels = [channel for channel, status in results.items() if status]
    
    if success_channels:
        return f"Notification sent successfully to: {', '.join(success_channels)}"
    else:
        return "Failed to send notification to any channel"


@tool
def send_slack_notification(
    message: str,
    title: Optional[str] = None,
    severity: str = "info"
) -> str:
    """
    Send a notification through Slack.
    
    Args:
        message: The message to send
        title: Optional title for the message
        severity: Severity level (info, warning, error)
    """
    success = notification_client.send_slack_notification(message, title, severity)
    return "Slack notification sent successfully" if success else "Failed to send Slack notification"


@tool
def send_teams_notification(
    message: str,
    title: Optional[str] = None,
    severity: str = "info"
) -> str:
    """
    Send a notification through Microsoft Teams.
    
    Args:
        message: The message to send
        title: Optional title for the message
        severity: Severity level (info, warning, error)
    """
    success = notification_client.send_teams_notification(message, title, severity)
    return "Teams notification sent successfully" if success else "Failed to send Teams notification"


@tool
def send_email_notification(
    message: str,
    subject: str,
    to_email: Optional[str] = None,
    severity: str = "info"
) -> str:
    """
    Send a notification through email.
    
    Args:
        message: The message to send
        subject: Email subject
        to_email: Recipient email address
        severity: Severity level (info, warning, error)
    """
    success = notification_client.send_email_notification(message, subject, to_email, severity)
    return "Email notification sent successfully" if success else "Failed to send email notification"


# List of all notification tools for easy import
notification_tools = [
    send_notification,
    send_slack_notification,
    send_teams_notification,
    send_email_notification
] 