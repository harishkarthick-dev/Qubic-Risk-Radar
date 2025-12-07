"""User authentication models"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User account"""
    
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Email verification
    is_verified = Column(Boolean, default=False, index=True)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Onboarding tracking
    onboarding_completed = Column(Boolean, default=False, server_default='false', nullable=False)
    onboarding_step = Column(Integer, default=1, server_default='1', nullable=False)
    webhook_test_received = Column(Boolean, default=False, server_default='false', nullable=False)
    
    # Notification settings
    discord_user_id = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    email_notifications_enabled = Column(Boolean, default=True, server_default='true', nullable=False)
    
    # Notification verification
    discord_verified = Column(Boolean, default=False, server_default='false', nullable=False)
    telegram_verified = Column(Boolean, default=False, server_default='false', nullable=False)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    easyconnect_configs = relationship("EasyConnectConfig", back_populates="user", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="user")
    rules = relationship("Rule", back_populates="user")
    monitored_targets = relationship("MonitoredTarget", back_populates="user")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_verified', 'is_verified'),
        Index('idx_users_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, verified={self.is_verified})>"
