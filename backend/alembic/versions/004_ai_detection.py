"""Add AI detection system tables

Revision ID: 004_ai_detection
Revises: 003_add_onboarding
Create Date: 2025-12-07

This migration adds tables for AI-powered detection:
- ai_detections: Stores AI analysis results for each event
- incidents: Redesigned incident tracking with AI integration
- notification_routing_rules: Smart notification routing configuration
- multi_scope_reports: Comprehensive analytics and reporting
- notification_logs: Delivery tracking and history
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic
revision = '004_ai_detection'
down_revision = '003_add_onboarding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ai_detections table
    op.create_table(
        'ai_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('normalized_events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # AI Detection Results
        sa.Column('anomaly_score', sa.Float, nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        
        # Classification
        sa.Column('primary_category', sa.String(100), nullable=False),
        sa.Column('sub_categories', postgresql.JSONB, nullable=True),
        sa.Column('scope', sa.String(50), nullable=False),
        
        # Analysis
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('detailed_analysis', sa.Text, nullable=True),
        sa.Column('detected_patterns', postgresql.JSONB, nullable=True),
        sa.Column('risk_factors', postgresql.JSONB, nullable=True),
        sa.Column('recommendations', postgresql.JSONB, nullable=True),
        sa.Column('related_addresses', postgresql.JSONB, nullable=True),
        
        # Metadata
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        
        sa.UniqueConstraint('event_id', name='uq_ai_detections_event')
    )
    
    # Indexes for ai_detections
    op.create_index('idx_ai_detections_user_severity', 'ai_detections', ['user_id', 'severity'])
    op.create_index('idx_ai_detections_category', 'ai_detections', ['primary_category'])
    op.create_index('idx_ai_detections_score', 'ai_detections', ['anomaly_score'])
    op.create_index('idx_ai_detections_created', 'ai_detections', ['created_at'])
    
    # incidents table (redesigned)
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_detections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Incident Info
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('scope', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        
        # Impact & Urgency
        sa.Column('impact_score', sa.Float, nullable=True),
        sa.Column('urgency', sa.String(20), nullable=True),
        
        # Timeline
        sa.Column('first_detected_at', sa.DateTime, nullable=False),
        sa.Column('last_updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        
        # User Management
        sa.Column('user_notes', sa.Text, nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=True),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        
        sa.UniqueConstraint('detection_id', name='uq_incidents_detection')
    )
    
    # Indexes for incidents
    op.create_index('idx_incidents_user', 'incidents', ['user_id'])
    op.create_index('idx_incidents_status', 'incidents', ['status'])
    op.create_index('idx_incidents_severity', 'incidents', ['severity'])
    op.create_index('idx_incidents_scope', 'incidents', ['scope'])
    op.create_index('idx_incidents_created', 'incidents', ['created_at'])
    
    # notification_routing_rules table
    op.create_table(
        'notification_routing_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Rule Conditions
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('incident_type', sa.String(100), nullable=True),
        sa.Column('scope', sa.String(50), nullable=True),
        
        # Channels Configuration
        sa.Column('discord_channel_id', sa.String(50), nullable=True),
        sa.Column('telegram_chat_id', sa.String(50), nullable=True),
        sa.Column('email_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('webhook_url', sa.Text, nullable=True),
        
        # Delivery Options
        sa.Column('notification_format', sa.String(50), nullable=False, server_default='minimal'),
        sa.Column('include_ai_analysis', sa.Boolean, nullable=False, server_default='true'),
        
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        
        sa.UniqueConstraint('user_id', 'severity', 'incident_type', 'scope', name='uq_routing_rules_user_conditions')
    )
    
    # Indexes for notification_routing_rules
    op.create_index('idx_routing_rules_user_enabled', 'notification_routing_rules', ['user_id', 'enabled'])
    op.create_index('idx_routing_rules_severity', 'notification_routing_rules', ['severity'])
    
    # multi_scope_reports table
    op.create_table(
        'multi_scope_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Report Configuration
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('scope', sa.String(50), nullable=False),
        sa.Column('time_range_start', sa.DateTime, nullable=False),
        sa.Column('time_range_end', sa.DateTime, nullable=False),
        
        # Aggregate Statistics
        sa.Column('total_events', sa.Integer, nullable=True),
        sa.Column('total_detections', sa.Integer, nullable=True),
        sa.Column('critical_count', sa.Integer, nullable=True),
        sa.Column('high_count', sa.Integer, nullable=True),
        sa.Column('medium_count', sa.Integer, nullable=True),
        sa.Column('low_count', sa.Integer, nullable=True),
        
        # AI Insights
        sa.Column('executive_summary', sa.Text, nullable=True),
        sa.Column('key_findings', postgresql.JSONB, nullable=True),
        sa.Column('anomaly_trends', postgresql.JSONB, nullable=True),
        sa.Column('pattern_summary', postgresql.JSONB, nullable=True),
        sa.Column('risk_assessment', sa.String(50), nullable=True),
        
        # Detailed Breakdowns
        sa.Column('by_category', postgresql.JSONB, nullable=True),
        sa.Column('by_severity', postgresql.JSONB, nullable=True),
        sa.Column('by_scope', postgresql.JSONB, nullable=True),
        sa.Column('by_contract', postgresql.JSONB, nullable=True),
        
        # Top Items
        sa.Column('top_addresses', postgresql.JSONB, nullable=True),
        sa.Column('top_contracts', postgresql.JSONB, nullable=True),
        sa.Column('top_patterns', postgresql.JSONB, nullable=True),
        
        # Actionable Insights
        sa.Column('recommendations', postgresql.JSONB, nullable=True),
        sa.Column('action_items', postgresql.JSONB, nullable=True),
        
        # Generation Metadata
        sa.Column('generated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('generation_time_ms', sa.Integer, nullable=True)
    )
    
    # Indexes for multi_scope_reports
    op.create_index('idx_reports_user', 'multi_scope_reports', ['user_id'])
    op.create_index('idx_reports_type_scope', 'multi_scope_reports', ['report_type', 'scope'])
    op.create_index('idx_reports_time_range', 'multi_scope_reports', ['time_range_start', 'time_range_end'])
    op.create_index('idx_reports_generated', 'multi_scope_reports', ['generated_at'])
    
    # notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('routing_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('notification_routing_rules.id', ondelete='SET NULL'), nullable=True),
        
        # Delivery Details
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('destination', sa.Text, nullable=False),
        sa.Column('severity', sa.String(20), nullable=True),
        
        # Status
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('delivered_at', sa.DateTime, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Indexes for notification_logs
    op.create_index('idx_notif_logs_user', 'notification_logs', ['user_id'])
    op.create_index('idx_notif_logs_incident', 'notification_logs', ['incident_id'])
    op.create_index('idx_notif_logs_status', 'notification_logs', ['status'])
    op.create_index('idx_notif_logs_created', 'notification_logs', ['created_at'])
    
    # Add columns to easyconnect_configs for multi-webhook support
    op.add_column('easyconnect_configs', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('easyconnect_configs', sa.Column('description', sa.Text, nullable=True))
    op.add_column('easyconnect_configs', sa.Column('tags', postgresql.JSONB, nullable=True))
    op.add_column('easyconnect_configs', sa.Column('routing_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('notification_routing_rules.id', ondelete='SET NULL'), nullable=True))
    op.add_column('easyconnect_configs', sa.Column('webhook_priority', sa.Integer, nullable=False, server_default='0'))
    op.add_column('easyconnect_configs', sa.Column('is_primary', sa.Boolean, nullable=False, server_default='false'))
    
    # Index for tags (GIN index for JSONB)
    op.create_index('idx_ec_configs_tags', 'easyconnect_configs', ['tags'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes and columns from easyconnect_configs
    op.drop_index('idx_ec_configs_tags', 'easyconnect_configs')
    op.drop_column('easyconnect_configs', 'is_primary')
    op.drop_column('easyconnect_configs', 'webhook_priority')
    op.drop_column('easyconnect_configs', 'routing_rule_id')
    op.drop_column('easyconnect_configs', 'tags')
    op.drop_column('easyconnect_configs', 'description')
    op.drop_column('easyconnect_configs', 'name')
    
    # Drop notification_logs
    op.drop_index('idx_notif_logs_created', 'notification_logs')
    op.drop_index('idx_notif_logs_status', 'notification_logs')
    op.drop_index('idx_notif_logs_incident', 'notification_logs')
    op.drop_index('idx_notif_logs_user', 'notification_logs')
    op.drop_table('notification_logs')
    
    # Drop multi_scope_reports
    op.drop_index('idx_reports_generated', 'multi_scope_reports')
    op.drop_index('idx_reports_time_range', 'multi_scope_reports')
    op.drop_index('idx_reports_type_scope', 'multi_scope_reports')
    op.drop_index('idx_reports_user', 'multi_scope_reports')
    op.drop_table('multi_scope_reports')
    
    # Drop notification_routing_rules
    op.drop_index('idx_routing_rules_severity', 'notification_routing_rules')
    op.drop_index('idx_routing_rules_user_enabled', 'notification_routing_rules')
    op.drop_table('notification_routing_rules')
    
    # Drop incidents
    op.drop_index('idx_incidents_created', 'incidents')
    op.drop_index('idx_incidents_scope', 'incidents')
    op.drop_index('idx_incidents_severity', 'incidents')
    op.drop_index('idx_incidents_status', 'incidents')
    op.drop_index('idx_incidents_user', 'incidents')
    op.drop_table('incidents')
    
    # Drop ai_detections
    op.drop_index('idx_ai_detections_created', 'ai_detections')
    op.drop_index('idx_ai_detections_score', 'ai_detections')
    op.drop_index('idx_ai_detections_category', 'ai_detections')
    op.drop_index('idx_ai_detections_user_severity', 'ai_detections')
    op.drop_table('ai_detections')
