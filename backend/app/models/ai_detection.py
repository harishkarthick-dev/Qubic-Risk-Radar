"""AI Detection models"""
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AIDetection(Base):
    """AI-powered detection results for blockchain events"""
    
    __tablename__ = "ai_detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('normalized_events.id', ondelete='CASCADE'), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # AI Detection Results
    anomaly_score = Column(Float, nullable=False)  # 0.0-1.0
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    
    # Classification
    primary_category = Column(String(100), nullable=False)
    sub_categories = Column(JSONB, nullable=True)
    scope = Column(String(50), nullable=False)  # network, protocol, wallet
    
    # Analysis
    summary = Column(Text, nullable=False)
    detailed_analysis = Column(Text, nullable=True)
    detected_patterns = Column(JSONB, nullable=True)
    risk_factors = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    related_addresses = Column(JSONB, nullable=True)
    
    # Metadata
    model_version = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Incident(Base):
    """Incident tracking with AI integration"""
    
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id = Column(UUID(as_uuid=True), ForeignKey('ai_detections.id', ondelete='CASCADE'), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Incident Info
    title = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False)
    scope = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default='open')
    
    # Impact & Urgency
    impact_score = Column(Float, nullable=True)
    urgency = Column(String(20), nullable=True)
    
    # Timeline
    first_detected_at = Column(DateTime, nullable=False)
    last_updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # User Management
    user_notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    assigned_to = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class NotificationRoutingRule(Base):
    """Smart notification routing configuration"""
    
    __tablename__ = "notification_routing_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Rule Conditions
    severity = Column(String(20), nullable=False)
    incident_type = Column(String(100), nullable=True)
    scope = Column(String(50), nullable=True)
    
    # Channels Configuration
    discord_channel_id = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    email_enabled = Column(String(50), nullable=False, server_default='false')
    webhook_url = Column(Text, nullable=True)
    
    # Delivery Options
    notification_format = Column(String(50), nullable=False, server_default='minimal')
    include_ai_analysis = Column(String(50), nullable=False, server_default='true')
    
    priority = Column(Integer, nullable=False, server_default='0')
    enabled = Column(String(50), nullable=False, server_default='true')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False, onupdate=func.now())


class NotificationLog(Base):
    """Notification delivery tracking"""
    
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey('incidents.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    routing_rule_id = Column(UUID(as_uuid=True), ForeignKey('notification_routing_rules.id', ondelete='SET NULL'), nullable=True)
    
    # Delivery Details
    channel = Column(String(50), nullable=False)
    destination = Column(Text, nullable=False)
    severity = Column(String(20), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, server_default='0')
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class MultiScopeReport(Base):
    """Multi-scope analytics reports"""
    
    __tablename__ = "multi_scope_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Report Configuration
    report_type = Column(String(50), nullable=False)
    scope = Column(String(50), nullable=False)
    time_range_start = Column(DateTime, nullable=False)
    time_range_end = Column(DateTime, nullable=False)
    
    # Aggregate Statistics
    total_events = Column(Integer, nullable=True)
    total_detections = Column(Integer, nullable=True)
    critical_count = Column(Integer, nullable=True)
    high_count = Column(Integer, nullable=True)
    medium_count = Column(Integer, nullable=True)
    low_count = Column(Integer, nullable=True)
    
    # AI Insights
    executive_summary = Column(Text, nullable=True)
    key_findings = Column(JSONB, nullable=True)
    anomaly_trends = Column(JSONB, nullable=True)
    pattern_summary = Column(JSONB, nullable=True)
    risk_assessment = Column(String(50), nullable=True)
    
    # Detailed Breakdowns
    by_category = Column(JSONB, nullable=True)
    by_severity = Column(JSONB, nullable=True)
    by_scope = Column(JSONB, nullable=True)
    by_contract = Column(JSONB, nullable=True)
    
    # Top Items
    top_addresses = Column(JSONB, nullable=True)
    top_contracts = Column(JSONB, nullable=True)
    top_patterns = Column(JSONB, nullable=True)
    
    # Actionable Insights
    recommendations = Column(JSONB, nullable=True)
    action_items = Column(JSONB, nullable=True)
    
    # Generation Metadata
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)
    model_version = Column(String(50), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
