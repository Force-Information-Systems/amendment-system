"""
Authentication module for JWT token generation and validation.

This module provides:
- JWT token creation and validation
- Password hashing and verification
- FastAPI dependencies for authentication and authorization
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        raise credentials_exception


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Employee:
    """
    FastAPI dependency to get the current authenticated user from token.

    Args:
        token: JWT token from request header
        db: Database session

    Returns:
        Employee object for the authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    employee_id: str = payload.get("sub")

    if employee_id is None:
        raise credentials_exception

    employee = (
        db.query(models.Employee)
        .filter(models.Employee.employee_id == int(employee_id))
        .first()
    )

    if employee is None:
        raise credentials_exception

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return employee


def require_admin(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
    """
    FastAPI dependency to require admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Employee object if user is admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def authenticate_windows_user(username: str, password: str) -> dict:
    """
    Authenticate a user against Active Directory using LDAP.

    This function attempts to bind to the AD server using the provided credentials.
    If successful, it retrieves user attributes from the directory.

    Args:
        username: Windows username (sAMAccountName)
        password: User's password

    Returns:
        Dictionary with user info if authentication successful:
        {
            'username': str,
            'email': str,
            'display_name': str
        }
        Returns None if authentication fails or AD is not configured.

    Note:
        Requires the following environment variables:
        - AD_ENABLED: Set to 'true' to enable AD authentication
        - AD_SERVER: LDAP server URL (e.g., ldap://dc.company.com)
        - AD_DOMAIN: Domain name (e.g., COMPANY)
        - AD_SEARCH_BASE: LDAP search base (e.g., DC=company,DC=com)
    """
    # Check if AD authentication is enabled FIRST (before importing ldap3)
    ad_enabled = os.getenv('AD_ENABLED', 'false').lower() == 'true'
    if not ad_enabled:
        return None

    # Only import ldap3 if AD is enabled (avoids import errors when AD is disabled)
    try:
        import ldap3
        from ldap3 import Server, Connection, ALL, NTLM
    except ImportError:
        print("Warning: ldap3 library not available, AD authentication disabled")
        return None

    ad_server = os.getenv('AD_SERVER')
    ad_domain = os.getenv('AD_DOMAIN')
    ad_search_base = os.getenv('AD_SEARCH_BASE')
    ad_use_ssl = os.getenv('AD_USE_SSL', 'false').lower() == 'true'

    if not all([ad_server, ad_domain, ad_search_base]):
        return None  # AD not properly configured

    try:
        # Create server object
        server = Server(ad_server, get_info=ALL, use_ssl=ad_use_ssl)

        # Construct user DN for authentication
        # Try NTLM format: DOMAIN\username
        user_dn = f"{ad_domain}\\{username}"

        # Attempt to bind with user credentials
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            authentication=NTLM,
            auto_bind=True
        )

        if not conn.bound:
            return None

        # Search for user attributes
        search_filter = f'(sAMAccountName={username})'
        conn.search(
            ad_search_base,
            search_filter,
            attributes=['mail', 'displayName', 'sAMAccountName', 'cn']
        )

        if conn.entries:
            entry = conn.entries[0]

            # Extract attributes
            email = str(entry.mail) if hasattr(entry, 'mail') and entry.mail else None
            display_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else None

            # Fallback to cn if displayName not available
            if not display_name:
                display_name = str(entry.cn) if hasattr(entry, 'cn') and entry.cn else username

            conn.unbind()

            return {
                'username': username,
                'email': email,
                'display_name': display_name
            }

        conn.unbind()
        return None

    except ldap3.core.exceptions.LDAPBindError:
        # Invalid credentials
        return None
    except ldap3.core.exceptions.LDAPException as e:
        # Other LDAP errors
        print(f"LDAP error: {e}")
        return None
    except Exception as e:
        # Catch-all for other errors
        print(f"AD authentication error: {e}")
        return None
