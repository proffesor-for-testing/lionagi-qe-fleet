"""
API Request and Response Factories

Generates realistic API request payloads and responses for testing
CI/CD webhook integrations, artifact uploads, and API interactions.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker

fake = Faker()


class APIRequestFactory:
    """Factory for generating API request payloads"""

    @staticmethod
    def create_webhook_payload(
        event_type: str = "push",
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        commit_count: int = 1,
    ) -> Dict[str, Any]:
        """Generate GitHub/GitLab-style webhook payload"""
        repo_name = repository or fake.slug()
        branch_name = branch or random.choice(["main", "develop", "feature/test", "hotfix/bug"])

        commits = [
            {
                "id": fake.sha256()[:40],
                "message": fake.sentence(),
                "author": {
                    "name": fake.name(),
                    "email": fake.email(),
                    "username": fake.user_name(),
                },
                "timestamp": fake.iso8601(),
                "added": [f"src/{fake.file_name(extension='py')}" for _ in range(random.randint(0, 3))],
                "modified": [f"tests/{fake.file_name(extension='py')}" for _ in range(random.randint(0, 5))],
                "removed": [f"docs/{fake.file_name(extension='md')}" for _ in range(random.randint(0, 2))],
            }
            for _ in range(commit_count)
        ]

        return {
            "event": event_type,
            "repository": {
                "id": random.randint(1000, 9999999),
                "name": repo_name,
                "full_name": f"{fake.user_name()}/{repo_name}",
                "url": f"https://github.com/{fake.user_name()}/{repo_name}",
                "default_branch": "main",
                "visibility": random.choice(["public", "private", "internal"]),
            },
            "ref": f"refs/heads/{branch_name}",
            "before": fake.sha256()[:40],
            "after": commits[-1]["id"] if commits else fake.sha256()[:40],
            "commits": commits,
            "pusher": {
                "name": fake.name(),
                "email": fake.email(),
            },
            "sender": {
                "login": fake.user_name(),
                "id": random.randint(1000, 9999999),
                "type": "User",
            },
            "created": False,
            "deleted": False,
            "forced": False,
            "compare": f"https://github.com/{fake.user_name()}/{repo_name}/compare/{fake.sha256()[:7]}...{fake.sha256()[:7]}",
        }

    @staticmethod
    def create_artifact_upload_request(
        artifact_type: str = "test-results",
        size_mb: float = 1.5,
    ) -> Dict[str, Any]:
        """Generate artifact upload request payload"""
        return {
            "artifact_id": str(uuid.uuid4()),
            "name": f"{artifact_type}-{fake.slug()}.zip",
            "type": artifact_type,
            "size_bytes": int(size_mb * 1024 * 1024),
            "checksum": {
                "algorithm": "sha256",
                "value": fake.sha256(),
            },
            "metadata": {
                "build_id": str(uuid.uuid4()),
                "job_name": fake.job(),
                "runner": random.choice(["ubuntu-latest", "macos-latest", "windows-latest"]),
                "timestamp": datetime.utcnow().isoformat(),
                "retention_days": random.randint(1, 90),
            },
            "compression": random.choice(["gzip", "zip", "none"]),
        }

    @staticmethod
    def create_test_execution_request(
        test_count: int = 100,
        framework: str = "pytest",
    ) -> Dict[str, Any]:
        """Generate test execution request payload"""
        return {
            "execution_id": str(uuid.uuid4()),
            "framework": framework,
            "configuration": {
                "parallel": random.choice([True, False]),
                "workers": random.randint(1, 8),
                "timeout": random.randint(300, 3600),
                "retries": random.randint(0, 3),
                "fail_fast": random.choice([True, False]),
            },
            "test_suite": {
                "path": "tests/",
                "pattern": f"test_*.{framework}",
                "count": test_count,
                "categories": {
                    "unit": int(test_count * 0.6),
                    "integration": int(test_count * 0.3),
                    "e2e": int(test_count * 0.1),
                },
            },
            "environment": {
                "python_version": random.choice(["3.10", "3.11", "3.12"]),
                "os": random.choice(["ubuntu-22.04", "macos-13", "windows-2022"]),
                "dependencies": [
                    {"name": fake.word(), "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 10)}"}
                    for _ in range(random.randint(5, 15))
                ],
            },
        }

    @classmethod
    def create_batch(cls, count: int, request_type: str = "webhook") -> List[Dict[str, Any]]:
        """Generate batch of requests"""
        generators = {
            "webhook": cls.create_webhook_payload,
            "artifact": cls.create_artifact_upload_request,
            "test": cls.create_test_execution_request,
        }
        generator = generators.get(request_type, cls.create_webhook_payload)
        return [generator() for _ in range(count)]


class APIResponseFactory:
    """Factory for generating API response payloads"""

    @staticmethod
    def create_success_response(
        data: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
    ) -> Dict[str, Any]:
        """Generate successful API response"""
        return {
            "status": "success",
            "status_code": status_code,
            "data": data or {"message": "Operation completed successfully"},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
        }

    @staticmethod
    def create_error_response(
        error_type: str = "validation_error",
        status_code: int = 400,
    ) -> Dict[str, Any]:
        """Generate error API response"""
        error_messages = {
            "validation_error": "Invalid request payload",
            "authentication_error": "Invalid or missing authentication token",
            "authorization_error": "Insufficient permissions",
            "rate_limit_error": "Rate limit exceeded",
            "server_error": "Internal server error",
            "timeout_error": "Request timeout",
        }

        return {
            "status": "error",
            "status_code": status_code,
            "error": {
                "type": error_type,
                "message": error_messages.get(error_type, "Unknown error"),
                "code": f"ERR_{status_code}_{error_type.upper()}",
                "details": {
                    "field": fake.word() if "validation" in error_type else None,
                    "reason": fake.sentence(),
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
        }

    @staticmethod
    def create_paginated_response(
        items: List[Any],
        page: int = 1,
        per_page: int = 10,
        total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate paginated API response"""
        total_items = total or len(items) * 5
        total_pages = (total_items + per_page - 1) // per_page

        return {
            "status": "success",
            "data": items[:per_page],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# Edge case and boundary value generators
class EdgeCaseAPIFactory:
    """Factory for edge case and boundary value API requests"""

    @staticmethod
    def create_empty_payload() -> Dict[str, Any]:
        """Generate empty payload"""
        return {}

    @staticmethod
    def create_null_values_payload() -> Dict[str, Any]:
        """Generate payload with null values"""
        return {
            "repository": None,
            "commits": None,
            "author": None,
            "timestamp": None,
        }

    @staticmethod
    def create_oversized_payload(size_mb: float = 10.0) -> Dict[str, Any]:
        """Generate oversized payload"""
        return {
            "artifact_id": str(uuid.uuid4()),
            "data": "x" * int(size_mb * 1024 * 1024),  # Oversized data field
            "size_bytes": int(size_mb * 1024 * 1024),
        }

    @staticmethod
    def create_malformed_json() -> str:
        """Generate malformed JSON string"""
        return '{"incomplete": "json", "missing'

    @staticmethod
    def create_special_characters_payload() -> Dict[str, Any]:
        """Generate payload with special characters"""
        return {
            "message": "Test with special chars: <>&\"'`\n\t\r",
            "path": "../../../etc/passwd",  # Path traversal attempt
            "script": "<script>alert('XSS')</script>",
            "sql": "'; DROP TABLE users; --",
            "unicode": "日本語🚀💻Ñoño",
        }

    @staticmethod
    def create_boundary_values() -> Dict[str, Any]:
        """Generate boundary value payload"""
        return {
            "integer_min": -2147483648,
            "integer_max": 2147483647,
            "integer_zero": 0,
            "float_min": float("-inf"),
            "float_max": float("inf"),
            "float_nan": float("nan"),
            "string_empty": "",
            "string_single": "a",
            "string_max": "x" * 65535,
            "array_empty": [],
            "array_single": [1],
            "array_large": list(range(10000)),
        }
