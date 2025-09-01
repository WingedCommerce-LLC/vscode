"""
Authentication module for Overseer platform.

This module provides JWT token management, password hashing,
role-based access control, and authentication utilities.
"""

from .password import verify_password, get_password_hash
from .jwt import create_access_token, verify_token, Token, TokenData
from .dependencies import get_current_user, get_current_active_user
from .permissions import require_role, require_admin

__all__ = [
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'verify_token',
    'Token',
    'TokenData',
    'get_current_user',
    'get_current_active_user',
    'require_role',
    'require_admin'
]
