"""System and UserSystem models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class System(Base):
    """System model for organizing documents."""

    __tablename__ = "systems"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # System identification
    name = Column(String(255), nullable=False)  # e.g., "system-a", "personal"
    display_name = Column(String(255), nullable=False)  # e.g., "System A"
    description = Column(String, nullable=True)

    # Personal system flag
    is_personal = Column(Boolean, default=False, index=True)
    owner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    # UI metadata
    icon = Column(String(100), nullable=True)  # e.g., "server", "database", "cloud"
    color = Column(String(7), nullable=True)  # Hex color code, e.g., "#3B82F6"

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    owner = relationship(
        "User",
        foreign_keys=[owner_user_id],
        back_populates="personal_systems",
    )
    creator = relationship("User", foreign_keys=[created_by])
    user_assignments = relationship(
        "UserSystem",
        back_populates="system",
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "Document",
        back_populates="system",
        cascade="all, delete-orphan",
    )
    tags = relationship(
        "Tag",
        back_populates="system",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "name",
            "is_personal",
            "owner_user_id",
            name="unique_system_name",
        ),
    )

    def __repr__(self) -> str:
        return f"<System(id={self.id}, name={self.name}, is_personal={self.is_personal})>"


class UserSystem(Base):
    """User-System assignment with permissions."""

    __tablename__ = "user_systems"

    # Composite primary key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("systems.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Permissions
    can_upload = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_query = Column(Boolean, default=True, nullable=False, index=True)

    # Assignment metadata
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="system_assignments")
    system = relationship("System", back_populates="user_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self) -> str:
        return (
            f"<UserSystem(user_id={self.user_id}, system_id={self.system_id}, "
            f"can_upload={self.can_upload}, can_query={self.can_query})>"
        )
