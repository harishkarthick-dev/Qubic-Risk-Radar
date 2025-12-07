"""Add authentication and multi-tenancy

Revision ID: 002_add_auth
Revises: 001_initial
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers
revision = '002_add_auth'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verification_token', sa.String(255)),
        sa.Column('verification_token_expires', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime())
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_verified', 'users', ['is_verified'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    
    # plans table
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('price_monthly', sa.Float(), default=0),
        sa.Column('price_yearly', sa.Float(), default=0),
        sa.Column('max_alerts', sa.Integer(), nullable=False),
        sa.Column('max_rules', sa.Integer(), nullable=False),
        sa.Column('max_monitored_contracts', sa.Integer(), nullable=False),
        sa.Column('features_json', postgresql.JSONB(), default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_plans_active', 'plans', ['is_active'])
    
    # subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='trial'),
        sa.Column('trial_ends_at', sa.DateTime()),
        sa.Column('next_billing_date', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_index('idx_subscriptions_user', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    
    # easyconnect_configs table
    op.create_table(
        'easyconnect_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_id', sa.String(255), nullable=False),
        sa.Column('webhook_secret', sa.String(255), nullable=False),
        sa.Column('contract_address', sa.String(255)),
        sa.Column('contract_label', sa.String(255)),
        sa.Column('event_type', sa.String(100)),
        sa.Column('conditions_json', postgresql.JSONB(), default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('description', sa.String(512)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    op.create_unique_constraint('uq_user_alert', 'easyconnect_configs', ['user_id', 'alert_id'])
    op.create_index('idx_ec_alert_id', 'easyconnect_configs', ['alert_id'])
    op.create_index('idx_ec_user_active', 'easyconnect_configs', ['user_id', 'is_active'])
    
    # Add user_id to existing tables
    op.add_column('incidents', sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('idx_incidents_user', 'incidents', ['user_id'])
    
    op.add_column('rules', sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('idx_rules_user', 'rules', ['user_id'])
    
    op.add_column('monitored_targets', sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('idx_monitored_user', 'monitored_targets', ['user_id'])
    
    # Drop old unique constraint on monitored_targets and add new one with user_id
    op.drop_constraint('uq_monitored_type_identifier', 'monitored_targets', type_='unique')
    op.create_unique_constraint('uq_user_monitored_type_identifier', 'monitored_targets', ['user_id', 'type', 'identifier'])
    
    # Seed data for plans
    plans_table = sa.table(
        'plans',
        sa.Column('name', sa.String),
        sa.Column('price_monthly', sa.Float),
        sa.Column('price_yearly', sa.Float),
        sa.Column('max_alerts', sa.Integer),
        sa.Column('max_rules', sa.Integer),
        sa.Column('max_monitored_contracts', sa.Integer),
        sa.Column('features_json', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean)
    )
    
    op.bulk_insert(plans_table, [
        {
            'name': 'Free',
            'price_monthly': 0.0,
            'price_yearly': 0.0,
            'max_alerts': 10,
            'max_rules': 5,
            'max_monitored_contracts': 2,
            'features_json': {
                'discord_notifications': True,
                'telegram_notifications': False,
                'email_notifications': False,
                'webhook_history_days': 7
            },
            'is_active': True
        },
        {
            'name': 'Pro',
            'price_monthly': 0.0,  # Free during trial
            'price_yearly': 0.0,
            'max_alerts': 200,
            'max_rules': 50,
            'max_monitored_contracts': 20,
            'features_json': {
                'discord_notifications': True,
                'telegram_notifications': True,
                'email_notifications': True,
                'webhook_history_days': 30,
                'advanced_rules': True,
                'api_access': True
            },
            'is_active': True
        },
        {
            'name': 'Enterprise',
            'price_monthly': 99.0,
            'price_yearly': 990.0,
            'max_alerts': -1,  # Unlimited
            'max_rules': -1,
            'max_monitored_contracts': -1,
            'features_json': {
                'all_pro_features': True,
                'custom_webhooks': True,
                'priority_support': True,
                'sla': True,
                'dedicated_support': True
            },
            'is_active': True
        }
    ])


def downgrade() -> None:
    # Remove user_id columns from existing tables
    op.drop_index('idx_monitored_user', table_name='monitored_targets')
    op.drop_constraint('uq_user_monitored_type_identifier', 'monitored_targets', type_='unique')
    op.drop_column('monitored_targets', 'user_id')
    op.create_unique_constraint('uq_monitored_type_identifier', 'monitored_targets', ['type', 'identifier'])
    
    op.drop_index('idx_rules_user', table_name='rules')
    op.drop_column('rules', 'user_id')
    
    op.drop_index('idx_incidents_user', table_name='incidents')
    op.drop_column('incidents', 'user_id')
    
    # Drop new tables
    op.drop_table('easyconnect_configs')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('users')
