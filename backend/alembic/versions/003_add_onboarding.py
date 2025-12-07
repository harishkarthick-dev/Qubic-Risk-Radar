"""Add onboarding and notification fields

Revision ID: 003_add_onboarding
Revises: 002_add_auth
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003_add_onboarding'
down_revision = '002_add_auth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add onboarding tracking fields
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('onboarding_step', sa.Integer(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('webhook_test_received', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Add notification settings
    op.add_column('users', sa.Column('discord_user_id', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('telegram_chat_id', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('email_notifications_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    
    # Add verification flags
    op.add_column('users', sa.Column('discord_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('telegram_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Create indexes for faster lookups
    op.create_index('idx_users_onboarding', 'users', ['onboarding_completed'])
    op.create_index('idx_users_discord', 'users', ['discord_user_id'])
    op.create_index('idx_users_telegram', 'users', ['telegram_chat_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_telegram', table_name='users')
    op.drop_index('idx_users_discord', table_name='users')
    op.drop_index('idx_users_onboarding', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'telegram_verified')
    op.drop_column('users', 'discord_verified')
    op.drop_column('users', 'email_notifications_enabled')
    op.drop_column('users', 'telegram_chat_id')
    op.drop_column('users', 'discord_user_id')
    op.drop_column('users', 'webhook_test_received')
    op.drop_column('users', 'onboarding_step')
    op.drop_column('users', 'onboarding_completed')
