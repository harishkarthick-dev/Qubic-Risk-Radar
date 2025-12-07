"""Alert model for notification delivery tracking"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base


class Alert(Base):
    """Notification delivery log"""
    
    __tablename__ = "alerts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Channel information
    channel = Column(String(50), nullable=False)  # discord, telegram, email
    target = Column(String(512))  # webhook URL, chat_id, email address
    
    # Delivery status
    sent_at = Column(DateTime, index=True)
    delivery_status = Column(String(50), default='pending', index=True)  # pending, sent, failed, retried
    
    # Payload and error tracking
    payload_summary = Column(String)
    error_message = Column(String)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="alerts")
    
    __table_args__ = (
        Index('idx_alerts_sent_at', 'sent_at'),
        Index('idx_alerts_status', 'delivery_status'),
    )
    
    def __repr__(self):
        return f"<Alert(id={self.id}, channel={self.channel}, status={self.delivery_status})>"
