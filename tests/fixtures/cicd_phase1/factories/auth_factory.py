"""
Authentication Token Factories

Generates various authentication tokens (JWT, OAuth2, API keys)
in valid, expired, and invalid states for testing authentication flows.
"""

import base64
import hashlib
import hmac
import json
import random
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from faker import Faker

fake = Faker()


class AuthTokenFactory:
    """Base factory for authentication tokens"""

    @staticmethod
    def generate_random_secret(length: int = 32) -> str:
        """Generate cryptographically secure random secret"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_token(token: str, algorithm: str = "sha256") -> str:
        """Hash token for storage"""
        return hashlib.new(algorithm, token.encode()).hexdigest()


class JWTTokenFactory(AuthTokenFactory):
    """Factory for JWT tokens"""

    SECRET_KEY = "test-secret-key-do-not-use-in-production"

    @staticmethod
    def create_valid_token(
        user_id: Optional[str] = None,
        expiry_hours: int = 24,
        scopes: Optional[list] = None,
    ) -> str:
        """Generate valid JWT token"""
        now = int(time.time())
        payload = {
            "sub": user_id or str(uuid.uuid4()),
            "iat": now,
            "exp": now + (expiry_hours * 3600),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "scopes": scopes or ["read", "write"],
            "user": {
                "id": user_id or str(uuid.uuid4()),
                "username": fake.user_name(),
                "email": fake.email(),
            },
        }

        # Mock JWT encoding (not cryptographically secure, for testing only)
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        # Mock signature
        message = f"{header_b64}.{payload_b64}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                JWTTokenFactory.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256,
            ).digest()
        ).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{signature}"

    @staticmethod
    def create_expired_token(expired_hours: int = 24) -> str:
        """Generate expired JWT token"""
        now = int(time.time())
        payload = {
            "sub": str(uuid.uuid4()),
            "iat": now - (expired_hours * 3600) - 3600,
            "exp": now - (expired_hours * 3600),
            "jti": str(uuid.uuid4()),
            "type": "access",
        }

        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        message = f"{header_b64}.{payload_b64}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                JWTTokenFactory.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256,
            ).digest()
        ).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{signature}"

    @staticmethod
    def create_invalid_token() -> str:
        """Generate invalid JWT token"""
        return f"{fake.sha256()[:22]}.{fake.sha256()[:32]}.{fake.sha256()[:43]}"

    @staticmethod
    def create_malformed_token() -> str:
        """Generate malformed JWT token"""
        return fake.sha256()  # Missing dots

    @staticmethod
    def create_token_with_invalid_signature() -> str:
        """Generate JWT token with invalid signature"""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(uuid.uuid4()),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        # Invalid signature
        signature = fake.sha256()[:43]

        return f"{header_b64}.{payload_b64}.{signature}"


class OAuth2TokenFactory(AuthTokenFactory):
    """Factory for OAuth2 tokens"""

    @staticmethod
    def create_access_token(
        token_type: str = "Bearer",
        expiry_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """Generate OAuth2 access token response"""
        return {
            "access_token": secrets.token_urlsafe(32),
            "token_type": token_type,
            "expires_in": expiry_seconds,
            "expires_at": int(time.time()) + expiry_seconds,
            "scope": "read write admin",
            "refresh_token": secrets.token_urlsafe(32),
        }

    @staticmethod
    def create_expired_access_token() -> Dict[str, Any]:
        """Generate expired OAuth2 access token"""
        return {
            "access_token": secrets.token_urlsafe(32),
            "token_type": "Bearer",
            "expires_in": -3600,
            "expires_at": int(time.time()) - 3600,
            "scope": "read write",
        }

    @staticmethod
    def create_refresh_token() -> Dict[str, Any]:
        """Generate OAuth2 refresh token"""
        return {
            "refresh_token": secrets.token_urlsafe(32),
            "token_type": "refresh",
            "expires_in": 2592000,  # 30 days
            "scope": "offline_access",
        }

    @staticmethod
    def create_authorization_code() -> str:
        """Generate OAuth2 authorization code"""
        return secrets.token_urlsafe(24)


class APIKeyFactory(AuthTokenFactory):
    """Factory for API keys"""

    @staticmethod
    def create_api_key(prefix: str = "ak", length: int = 32) -> str:
        """Generate API key with prefix"""
        return f"{prefix}_{secrets.token_urlsafe(length)}"

    @staticmethod
    def create_api_key_pair() -> Dict[str, str]:
        """Generate API key ID and secret pair"""
        key_id = f"akid_{secrets.token_urlsafe(16)}"
        key_secret = secrets.token_urlsafe(32)
        return {
            "key_id": key_id,
            "key_secret": key_secret,
            "key_hash": AuthTokenFactory.hash_token(key_secret),
        }

    @staticmethod
    def create_github_token() -> str:
        """Generate GitHub-style personal access token"""
        return f"ghp_{secrets.token_urlsafe(36)}"

    @staticmethod
    def create_gitlab_token() -> str:
        """Generate GitLab-style personal access token"""
        return f"glpat-{secrets.token_urlsafe(20)}"

    @staticmethod
    def create_webhook_secret() -> str:
        """Generate webhook signing secret"""
        return secrets.token_hex(32)


# Edge case tokens
class EdgeCaseTokenFactory:
    """Factory for edge case authentication tokens"""

    @staticmethod
    def create_empty_token() -> str:
        """Generate empty token"""
        return ""

    @staticmethod
    def create_whitespace_token() -> str:
        """Generate whitespace-only token"""
        return "   \t\n  "

    @staticmethod
    def create_special_characters_token() -> str:
        """Generate token with special characters"""
        return "!@#$%^&*(){}[]|\\:;\"'<>,.?/"

    @staticmethod
    def create_sql_injection_token() -> str:
        """Generate SQL injection attempt token"""
        return "' OR '1'='1'; DROP TABLE users; --"

    @staticmethod
    def create_xss_token() -> str:
        """Generate XSS attempt token"""
        return "<script>alert('XSS')</script>"

    @staticmethod
    def create_path_traversal_token() -> str:
        """Generate path traversal attempt token"""
        return "../../../etc/passwd"

    @staticmethod
    def create_null_byte_token() -> str:
        """Generate token with null byte"""
        return f"valid_token\x00malicious_data"

    @staticmethod
    def create_unicode_token() -> str:
        """Generate token with unicode characters"""
        return f"token_日本語_🚀_{secrets.token_urlsafe(16)}"

    @staticmethod
    def create_oversized_token(size_kb: int = 10) -> str:
        """Generate oversized token"""
        return "x" * (size_kb * 1024)


# Token state manager for testing
class TokenStateManager:
    """Manager for tracking token states in tests"""

    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def register_token(
        self,
        token: str,
        state: str = "valid",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Register token with state"""
        self.tokens[token] = {
            "state": state,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
        }

    def get_token_state(self, token: str) -> Optional[str]:
        """Get token state"""
        return self.tokens.get(token, {}).get("state")

    def revoke_token(self, token: str):
        """Revoke token"""
        if token in self.tokens:
            self.tokens[token]["state"] = "revoked"
            self.tokens[token]["revoked_at"] = datetime.utcnow()

    def create_token_set(self) -> Dict[str, str]:
        """Create set of tokens in various states"""
        tokens = {
            "valid": JWTTokenFactory.create_valid_token(),
            "expired": JWTTokenFactory.create_expired_token(),
            "invalid": JWTTokenFactory.create_invalid_token(),
            "malformed": JWTTokenFactory.create_malformed_token(),
        }

        for name, token in tokens.items():
            self.register_token(token, state=name)

        return tokens
