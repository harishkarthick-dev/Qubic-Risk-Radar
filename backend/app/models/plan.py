"""Subscription plan models"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Plan(Base):
    """Subscription plan (Free, Pro, Enterprise)"""
    
    __tablename__ = "plans"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False, unique=True)
    
    # Pricing
    price_monthly = Column(Float, default=0)
    price_yearly = Column(Float, default=0)
    
    # Limits
    max_alerts = Column(Integer, nullable=False)  # -1 for unlimited
    max_rules = Column(Integer, nullable=False)
    max_monitored_contracts = Column(Integer, nullable=False)
    
    # Features (JSON for flexibility)
    features_json = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name})>"


class Subscription(Base):
    """User subscription to a plan"""
    
    __tablename__ = "subscriptions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    plan_id = Column(PGUUID(as_uuid=True), ForeignKey('plans.id', ondelete='RESTRICT'), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default='trial', index=True)  # trial, active, expired, cancelled
    
    # Trial period
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Billing
    next_billing_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")
    
    __table_args__ = (
        Index('idx_subscriptions_user', 'user_id'),
        Index('idx_subscriptions_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan.name if self.plan else 'N/A'}, status={self.status})>"
