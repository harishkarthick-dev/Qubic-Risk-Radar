"""Rule model for detection logic"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base


class Rule(Base):
    """Detection rule for identifying blockchain anomalies"""
    
    __tablename__ = "rules"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
    
    # Severity and categorization
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, CRITICAL
    type = Column(String(100))  # WhaleTransfer, FailureSpike, VolumeAnomaly, etc.
    scope = Column(String(50))  # network, protocol, wallet
    
    # Rule logic
    conditions_json = Column(JSON, nullable=False)  # Matching conditions
    aggregation_window_seconds = Column(Integer, default=60)
    thresholds_json = Column(JSON)  # Statistical thresholds
    
    # Deduplication and cooldown
    deduplication_key_template = Column(String(512))
    cooldown_seconds = Column(Integer, default=300)
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rules")
    incidents = relationship("Incident", back_populates="rule")
    
    __table_args__ = (
        Index('idx_rules_enabled', 'enabled'),
        Index('idx_rules_severity', 'severity'),
    )
    
    def __repr__(self):
        return f"<Rule(id={self.id}, name={self.name}, severity={self.severity}, enabled={self.enabled})>"
