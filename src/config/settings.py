"""
Configuration settings for the K8s monitoring agent.
Loads settings from environment variables with support for .env files.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    openai_model: str = Field('gpt-4-turbo-preview', env='OPENAI_MODEL')
    openai_api_base: str = Field('https://api.openai.com/v1', env='OPENAI_API_BASE')
    
    # Kubernetes Configuration
    kubernetes_context: str = Field('default', env='KUBERNETES_CONTEXT')
    kubernetes_namespace: str = Field('default', env='KUBERNETES_NAMESPACE')
    monitoring_interval: int = Field(300, env='MONITORING_INTERVAL')  # seconds
    
    # ChromaDB Configuration
    chroma_persist_dir: Path = Field(
        BASE_DIR / 'data' / 'chromadb',
        env='CHROMA_PERSIST_DIR'
    )
    embedding_model: str = Field('all-MiniLM-L6-v2', env='EMBEDDING_MODEL')
    
    # Notification Configuration
    notification_channels: str = Field(
        'slack',
        env='NOTIFICATION_CHANNELS'
    )
    slack_webhook_url: Optional[str] = Field(None, env='SLACK_WEBHOOK_URL')
    teams_webhook_url: Optional[str] = Field(None, env='TEAMS_WEBHOOK_URL')
    smtp_host: Optional[str] = Field(None, env='SMTP_HOST')
    smtp_port: Optional[int] = Field(None, env='SMTP_PORT')
    smtp_username: Optional[str] = Field(None, env='SMTP_USERNAME')
    smtp_password: Optional[str] = Field(None, env='SMTP_PASSWORD')
    notification_email: Optional[str] = Field(None, env='NOTIFICATION_EMAIL')
    
    # Logging Configuration
    log_level: str = Field('INFO', env='LOG_LEVEL')
    log_file: Path = Field(BASE_DIR / 'logs' / 'agent.log', env='LOG_FILE')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create necessary directories
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse notification channels
        if isinstance(self.notification_channels, str):
            # Handle comma-separated string
            if ',' in self.notification_channels:
                self.notification_channels = [
                    channel.strip()
                    for channel in self.notification_channels.split(',')
                ]
            # Handle single string
            else:
                self.notification_channels = [self.notification_channels.strip()]

# Create global settings instance
settings = Settings() 