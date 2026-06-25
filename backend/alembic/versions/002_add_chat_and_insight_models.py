"""Add chat and insight models

Revision ID: 002
Revises: 001
Create Date: 2026-06-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # AgentChat
    op.create_table('agent_chats',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_chats_user_id'), 'agent_chats', ['user_id'], unique=False)

    # ChatMessage
    op.create_table('chat_messages',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('chat_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('tool_calls', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['agent_chats.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_chat_id'), 'chat_messages', ['chat_id'], unique=False)

    # StoredInsight
    op.create_table('stored_insights',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('insight_type', sa.String(length=50), nullable=False),
    sa.Column('reference_id', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stored_insights_insight_type'), 'stored_insights', ['insight_type'], unique=False)
    op.create_index(op.f('ix_stored_insights_reference_id'), 'stored_insights', ['reference_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stored_insights_reference_id'), table_name='stored_insights')
    op.drop_index(op.f('ix_stored_insights_insight_type'), table_name='stored_insights')
    op.drop_table('stored_insights')
    op.drop_index(op.f('ix_chat_messages_chat_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index(op.f('ix_agent_chats_user_id'), table_name='agent_chats')
    op.drop_table('agent_chats')
