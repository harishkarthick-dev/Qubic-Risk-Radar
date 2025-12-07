"""Initial schema with all tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('received_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(), nullable=False),
        sa.Column('signature', sa.String(512)),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_events_received_at', 'events', ['received_at'])
    op.create_index('idx_events_status', 'events', ['status'])
    op.create_index('idx_events_source', 'events', ['source'])
    
    # rules table
    op.create_table(
        'rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.String()),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('type', sa.String(100)),
        sa.Column('scope', sa.String(50)),
        sa.Column('conditions_json', postgresql.JSONB(), nullable=False),
        sa.Column('aggregation_window_seconds', sa.Integer(), server_default='60'),
        sa.Column('thresholds_json', postgresql.JSONB()),
        sa.Column('deduplication_key_template', sa.String(512)),
        sa.Column('cooldown_seconds', sa.Integer(), server_default='300'),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_rules_enabled', 'rules', ['enabled'])
    op.create_index('idx_rules_severity', 'rules', ['severity'])
    
    # normalized_events table
    op.create_table(
        'normalized_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id', ondelete='CASCADE')),
        sa.Column('chain', sa.String(50), server_default='QUBIC'),
        sa.Column('contract_address', sa.String(255)),
        sa.Column('contract_label', sa.String(255)),
        sa.Column('event_name', sa.String(100)),
        sa.Column('tx_hash', sa.String(512)),
        sa.Column('tx_status', sa.String(50)),
        sa.Column('from_address', sa.String(255)),
        sa.Column('to_address', sa.String(255)),
        sa.Column('amount', sa.BigInteger()),
        sa.Column('token_symbol', sa.String(50), server_default='QUBIC'),
        sa.Column('block_height', sa.BigInteger()),
        sa.Column('tick', sa.BigInteger()),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_norm_events_timestamp', 'normalized_events', ['timestamp'])
    op.create_index('idx_norm_events_contract_ts', 'normalized_events', ['contract_address', 'timestamp'])
    op.create_index('idx_norm_events_from_ts', 'normalized_events', ['from_address', 'timestamp'])
    op.create_index('idx_norm_events_to_ts', 'normalized_events', ['to_address', 'timestamp'])
    op.create_index('idx_norm_events_tx_status', 'normalized_events', ['tx_status', 'timestamp'])
    op.create_index('idx_norm_events_event_name', 'normalized_events', ['event_name'])
    
    # incidents table
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('protocol', sa.String(100)),
        sa.Column('contract_address', sa.String(255)),
        sa.Column('primary_wallet', sa.String(255)),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rules.id', ondelete='SET NULL')),
        sa.Column('deduplication_key', sa.String(512)),
        sa.Column('metadata_json', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_incidents_severity_first', 'incidents', ['severity', 'first_seen_at'])
    op.create_index('idx_incidents_status', 'incidents', ['status'])
    op.create_index('idx_incidents_protocol', 'incidents', ['protocol', 'first_seen_at'])
    op.create_index('idx_incidents_dedup_key', 'incidents', ['deduplication_key'])
    op.create_index('idx_incidents_contract', 'incidents', ['contract_address'])
    
    # incident_events junction table
    op.create_table(
        'incident_events',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('normalized_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('normalized_events.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_incident_events_incident', 'incident_events', ['incident_id'])
    op.create_index('idx_incident_events_event', 'incident_events', ['normalized_event_id'])
    
    # alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('target', sa.String(512)),
        sa.Column('sent_at', sa.DateTime()),
        sa.Column('delivery_status', sa.String(50), server_default='pending'),
        sa.Column('payload_summary', sa.String()),
        sa.Column('error_message', sa.String()),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_alerts_incident', 'alerts', ['incident_id'])
    op.create_index('idx_alerts_sent_at', 'alerts', ['sent_at'])
    op.create_index('idx_alerts_status', 'alerts', ['delivery_status'])
    
    # monitored_targets table
    op.create_table(
        'monitored_targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('label', sa.String(255)),
        sa.Column('metadata_json', postgresql.JSONB()),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_unique_constraint('uq_monitored_type_identifier', 'monitored_targets', ['type', 'identifier'])
    op.create_index('idx_monitored_type_enabled', 'monitored_targets', ['type', 'enabled'])
    op.create_index('idx_monitored_identifier', 'monitored_targets', ['identifier'])


def downgrade() -> None:
    op.drop_table('monitored_targets')
    op.drop_table('alerts')
    op.drop_table('incident_events')
    op.drop_table('incidents')
    op.drop_table('normalized_events')
    op.drop_table('rules')
    op.drop_table('events')
