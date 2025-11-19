"""FastAPI dependencies for authentication and authorization."""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token, verify_token_type
from app.models.user import User

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database session

    Returns:
        Current authenticated User

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        token = credentials.credentials
        payload = decode_token(token)

        # Verify it's an access token (not refresh)
        if not verify_token_type(payload, "access"):
            raise credentials_exception

        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for get_current_user).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current active user
    """
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to be an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def require_doc_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to be a document manager or admin.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if doc manager or admin

    Raises:
        HTTPException: If user is not a doc manager or admin
    """
    if not (current_user.is_doc_manager or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document manager privileges required"
        )
    return current_user


def require_super_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to be a super user or admin.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if super user or admin

    Raises:
        HTTPException: If user is not a super user or admin
    """
    if not (current_user.is_super_user or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super user privileges required"
        )
    return current_user
