"""SQLAlchemy models for Ask My Docs.

All models must be imported here so SQLAlchemy can discover them
and Alembic can generate migrations.
"""

from app.models.analytics import AuditLog, Export, QAAnalytics, UserFeedback
from app.models.agent_execution import AgentExecution, AgentFilesystem
from app.models.conversation import Conversation, Message, MessageEdit
from app.models.document import Document, DocumentChunk, DocumentTag, Tag
from app.models.system import System, UserSystem
from app.models.user import User, UserRole

__all__ = [
    # User models
    "User",
    "UserRole",
    # System models
    "System",
    "UserSystem",
    # Document models
    "Document",
    "DocumentChunk",
    "Tag",
    "DocumentTag",
    # Conversation models
    "Conversation",
    "Message",
    "MessageEdit",
    # Agent execution models (HITL core)
    "AgentExecution",
    "AgentFilesystem",
    # Analytics models
    "QAAnalytics",
    "UserFeedback",
    "Export",
    "AuditLog",
]
