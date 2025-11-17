"""User model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles for permission management."""

    ADMIN = "admin"
    DOC_MANAGER = "doc_manager"
    SYSTEM_USER = "system_user"
    SUPER_USER = "super_user"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))

    # Authorization
    role = Column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.SYSTEM_USER,
        index=True,
    )

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_login_at = Column(DateTime, nullable=True)

    # Preferences (JSONB for flexibility)
    preferences = Column(
        JSONB,
        default=lambda: {
            "theme": "light",
            "notifications_enabled": True,
            "default_systems": [],
        },
        nullable=False,
    )

    # Relationships
    system_assignments = relationship(
        "UserSystem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    personal_systems = relationship(
        "System",
        foreign_keys="System.owner_user_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents_uploaded = relationship(
        "Document",
        foreign_keys="Document.uploaded_by",
        back_populates="uploader",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_doc_manager(self) -> bool:
        """Check if user is a document manager."""
        return self.role == UserRole.DOC_MANAGER

    @property
    def is_super_user(self) -> bool:
        """Check if user is a super user."""
        return self.role == UserRole.SUPER_USER
