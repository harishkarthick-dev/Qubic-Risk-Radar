"""Incident models for detected anomalies"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Incident(Base):
    """Detected blockchain anomaly or event of interest"""
    
    __tablename__ = "incidents"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # User ownership
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Severity and status
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, CRITICAL
    status = Column(String(50), default='open', index=True)  # open, acknowledged, resolved
    
    # Classification
    type = Column(String(100), nullable=False)  # WhaleTransfer, FailureSpike, etc.
    title = Column(String(255), nullable=False)
    description = Column(String)
    
    # Context
    protocol = Column(String(100), index=True)
    contract_address = Column(String(255), index=True)
    primary_wallet = Column(String(255))
    
    # Timing
    first_seen_at = Column(DateTime, nullable=False, index=True)
    last_seen_at = Column(DateTime, nullable=False)
    
    # Rule association
    rule_id = Column(PGUUID(as_uuid=True), ForeignKey('rules.id', ondelete='SET NULL'), nullable=True)
    
    # Deduplication
    deduplication_key = Column(String(512), index=True)
    
    # Additional metadata
    metadata_json = Column(JSON)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="incidents")
    rule = relationship("Rule", back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")
    incident_events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_incidents_severity_first', 'severity', 'first_seen_at'),
        Index('idx_incidents_protocol', 'protocol', 'first_seen_at'),
        Index('idx_incidents_dedup_key', 'deduplication_key'),
    )
    
    def __repr__(self):
        return f"<Incident(id={self.id}, severity={self.severity}, type={self.type}, status={self.status})>"


class IncidentEvent(Base):
    """Junction table linking incidents to normalized events"""
    
    __tablename__ = "incident_events"
    
    incident_id = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True)
    normalized_event_id = Column(PGUUID(as_uuid=True), ForeignKey('normalized_events.id', ondelete='CASCADE'), primary_key=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="incident_events")
    normalized_event = relationship("NormalizedEvent", back_populates="incident_events")
    
    __table_args__ = (
        Index('idx_incident_events_incident', 'incident_id'),
        Index('idx_incident_events_event', 'normalized_event_id'),
    )
    
    def __repr__(self):
        return f"<IncidentEvent(incident_id={self.incident_id}, event_id={self.normalized_event_id})>"
