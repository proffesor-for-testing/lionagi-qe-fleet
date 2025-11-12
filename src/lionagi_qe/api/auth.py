"""
Authentication and authorization for API endpoints.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Header, status
from jose import JWTError, jwt
from pydantic import BaseModel


class APIKey(BaseModel):
    """API key model."""

    key: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    rate_limit: int = 100  # requests per minute
    enabled: bool = True


class TokenData(BaseModel):
    """JWT token payload."""

    api_key: str
    expires: datetime


# Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory API key storage (replace with database in production)
_api_keys: Dict[str, APIKey] = {}


def generate_api_key(name: str = "default") -> str:
    """
    Generate a new API key.

    Args:
        name: Human-readable name for the API key

    Returns:
        Generated API key string
    """
    # Generate secure random key
    key = f"aqe_{secrets.token_urlsafe(32)}"

    # Hash for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    # Store API key
    _api_keys[key_hash] = APIKey(
        key=key_hash, name=name, created_at=datetime.utcnow()
    )

    return key


def get_api_key_hash(api_key: str) -> str:
    """
    Get hash of API key for lookup.

    Note: SHA-256 is used here for API key lookup/storage only, not for password hashing.
    For password hashing, use bcrypt, scrypt, or Argon2 instead.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str) -> Optional[APIKey]:
    """
    Verify API key and return associated data.

    Args:
        api_key: API key to verify

    Returns:
        APIKey object if valid, None otherwise
    """
    key_hash = get_api_key_hash(api_key)
    key_data = _api_keys.get(key_hash)

    if key_data and key_data.enabled:
        # Update last used timestamp
        key_data.last_used = datetime.utcnow()
        return key_data

    return None


def create_access_token(api_key: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        api_key: API key to encode in token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {"api_key": api_key, "exp": expire}

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token to decode

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        api_key: str = payload.get("api_key")
        expires: datetime = datetime.fromtimestamp(payload.get("exp"))

        if api_key is None:
            return None

        return TokenData(api_key=api_key, expires=expires)
    except JWTError:
        return None


async def verify_api_key_header(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> APIKey:
    """
    FastAPI dependency for API key verification.

    Args:
        authorization: Authorization header value

    Returns:
        APIKey object if valid

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Support both "Bearer <token>" and "Bearer <api_key>" formats
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_or_key = parts[1]

    # Try as JWT token first
    if not token_or_key.startswith("aqe_"):
        token_data = decode_access_token(token_or_key)
        if token_data:
            # Verify the API key from token
            key_data = verify_api_key(token_data.api_key)
            if key_data:
                return key_data

    # Try as direct API key
    key_data = verify_api_key(token_or_key)
    if key_data:
        return key_data

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_api_key(
    api_key: APIKey = Depends(verify_api_key_header),
) -> APIKey:
    """
    FastAPI dependency to get current API key.

    Args:
        api_key: Verified API key from header

    Returns:
        APIKey object
    """
    return api_key


# Initialize default API key for testing
if not _api_keys:
    default_key = generate_api_key("default-test-key")
    # Security: Never log API keys in production. Masked for security.
    print(f"Generated default API key: {default_key[:8]}{'*' * 24}")
    print("Use this key for testing: curl -H 'Authorization: Bearer <key>'")
