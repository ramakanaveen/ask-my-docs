"""Initial schema with all 15 tables and PGVector support

Revision ID: 82a282de20a4
Revises:
Create Date: 2025-11-19 22:16:02.292568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '82a282de20a4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create all 15 tables."""

    # Enable PGVector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='system_user', index=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('preferences', postgresql.JSONB, nullable=True),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # 2. Systems table
    op.create_table(
        'systems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_personal', sa.Boolean, nullable=False, server_default='false', index=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('settings', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('owner_id', 'name', name='unique_system_per_owner'),
    )

    # 3. User-System join table (permissions)
    op.create_table(
        'user_systems',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('can_upload', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_edit', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_query', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('added_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # 4. Documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False, index=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('parent_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('processing_started_at', sa.DateTime, nullable=True),
        sa.Column('processing_completed_at', sa.DateTime, nullable=True),
        sa.Column('processing_error', sa.Text, nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('word_count', sa.Integer, nullable=True),
        sa.Column('extracted_metadata', postgresql.JSONB, nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('uploaded_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('last_edited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_edited_at', sa.DateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # 5. Document Chunks table (with PGVector)
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True, index=True),
        sa.Column('start_char_index', sa.Integer, nullable=True),
        sa.Column('end_char_index', sa.Integer, nullable=True),
        sa.Column('page_number', sa.Integer, nullable=True),
        sa.Column('section_title', sa.String(500), nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=False, server_default='text-embedding-3-small'),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('embedded_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('document_id', 'chunk_index', name='unique_chunk_per_document'),
    )

    # 6. Tags table
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('system_id', 'name', name='unique_tag_per_system'),
    )

    # 7. Document-Tag join table
    op.create_table(
        'document_tags',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('added_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # 8. Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active', index=True),
        sa.Column('started_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime, nullable=True),
    )

    # 9. Messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('rich_content', postgresql.JSONB, nullable=True),
        sa.Column('agent_execution_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('current_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # 10. Message Edits table
    op.create_table(
        'message_edits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('rich_content', postgresql.JSONB, nullable=True),
        sa.Column('edited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('edited_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('edit_reason', sa.String(500), nullable=True),
        sa.UniqueConstraint('message_id', 'version', name='unique_message_version'),
    )

    # 11. Agent Executions table (HITL Core)
    op.create_table(
        'agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('planning_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('filesystem_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.String(50), nullable=False, server_default='running', index=True),
        sa.Column('started_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('hitl_paused_at', sa.DateTime, nullable=True),
        sa.Column('hitl_approved_at', sa.DateTime, nullable=True),
        sa.Column('hitl_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('plan_json', postgresql.JSONB, nullable=True),
        sa.Column('total_duration_ms', sa.Integer, nullable=True),
        sa.Column('llm_calls_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_tokens_used', sa.Integer, nullable=False, server_default='0'),
        sa.Column('tools_called', postgresql.JSONB, nullable=True),
        sa.Column('subagents_used', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_stack_trace', sa.Text, nullable=True),
    )

    # Add FK constraint for message -> agent_execution (circular reference)
    op.create_foreign_key(
        'fk_messages_agent_execution_id',
        'messages',
        'agent_executions',
        ['agent_execution_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 12. Agent Filesystem table
    op.create_table(
        'agent_filesystem',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_executions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('execution_id', 'file_path', name='unique_file_per_execution'),
    )

    # 13. QA Analytics table
    op.create_table(
        'qa_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('systems.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('documents_referenced', postgresql.JSONB, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('was_edited_by_human', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('hitl_approved', sa.Boolean, nullable=True),
        sa.Column('asked_at', sa.DateTime, nullable=False, server_default=sa.text('now()'), index=True),
    )

    # 14. User Feedback table
    op.create_table(
        'user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('feedback_text', sa.Text, nullable=True),
        sa.Column('correction', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # 15. Exports table
    op.create_table(
        'exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('export_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # 16. Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()'), index=True),
    )

    # Create indexes for PGVector similarity search
    op.create_index(
        'idx_document_chunks_embedding',
        'document_chunks',
        ['embedding'],
        postgresql_using='ivfflat',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('audit_logs')
    op.drop_table('exports')
    op.drop_table('user_feedback')
    op.drop_table('qa_analytics')
    op.drop_table('agent_filesystem')
    op.drop_table('agent_executions')
    op.drop_table('message_edits')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_tags')
    op.drop_table('tags')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('user_systems')
    op.drop_table('systems')
    op.drop_table('users')

    # Drop PGVector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
