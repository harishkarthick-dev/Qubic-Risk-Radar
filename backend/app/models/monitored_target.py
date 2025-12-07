"""Monitored target model for watchlists"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.database import Base


class MonitoredTarget(Base):
    """Watchlist entry for contracts, wallets, or protocols"""
    
    __tablename__ = "monitored_targets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Target classification
    type = Column(String(50), nullable=False)  # contract, wallet, protocol
    identifier = Column(String(255), nullable=False)  # Address or protocol name
    label = Column(String(255))  # Human-readable name
    
    # Additional metadata
    metadata_json = Column(JSON)
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="monitored_targets")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'type', 'identifier', name='uq_user_monitored_type_identifier'),
        Index('idx_monitored_type_enabled', 'type', 'enabled'),
        Index('idx_monitored_identifier', 'identifier'),
    )
    
    def __repr__(self):
        return f"<MonitoredTarget(id={self.id}, type={self.type}, identifier={self.identifier}, label={self.label})>"
