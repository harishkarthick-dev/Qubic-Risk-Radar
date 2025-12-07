"""Event models for raw and normalized blockchain events"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, JSON, BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base


class Event(Base):
    """Raw event from EasyConnect webhook"""
    
    __tablename__ = "events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = Column(String(255), nullable=False, index=True)  # 'easyconnect:alert_uuid'
    payload_json = Column(JSON, nullable=False)
    signature = Column(String(512), nullable=True)
    status = Column(String(50), default='pending', index=True)  # pending, parsed, failed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    normalized_events = relationship("NormalizedEvent", back_populates="event", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_events_received_at', 'received_at'),
        Index('idx_events_status', 'status'),
        Index('idx_events_source', 'source'),
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, source={self.source}, status={self.status})>"


class NormalizedEvent(Base):
    """Parsed and normalized blockchain event"""
    
    __tablename__ = "normalized_events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(PGUUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=True)
    
    # Blockchain data
    chain = Column(String(50), default='QUBIC')
    contract_address = Column(String(255), index=True)
    contract_label = Column(String(255))  # 'QX', 'Quottery', etc.
    event_name = Column(String(100), index=True)  # 'Transfer', 'AddToBidOrder'
    
    # Transaction data
    tx_hash = Column(String(512))
    tx_status = Column(String(50), index=True)  # 'success', 'failure'
    from_address = Column(String(255), index=True)
    to_address = Column(String(255), index=True)
    
    # Value data
    amount = Column(BigInteger)  # Amount in smallest units
    token_symbol = Column(String(50), default='QUBIC')
    
    # Block data
    block_height = Column(BigInteger)
    tick = Column(BigInteger)  # Qubic-specific
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Additional metadata
    metadata_json = Column(JSON)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="normalized_events")
    incident_events = relationship("IncidentEvent", back_populates="normalized_event", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_norm_events_timestamp', 'timestamp'),
        Index('idx_norm_events_contract_ts', 'contract_address', 'timestamp'),
        Index('idx_norm_events_from_ts', 'from_address', 'timestamp'),
        Index('idx_norm_events_to_ts', 'to_address', 'timestamp'),
        Index('idx_norm_events_tx_status', 'tx_status', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<NormalizedEvent(id={self.id}, event_name={self.event_name}, contract={self.contract_label})>"
