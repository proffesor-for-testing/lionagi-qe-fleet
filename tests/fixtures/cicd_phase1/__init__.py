"""
CI/CD Phase 1 Test Data Management

Comprehensive test data generation, management, and compliance framework
for CI/CD integration testing.

Modules:
- factories: Test data factories using Factory Boy and Faker
- generators: Custom data generators for specialized scenarios
- seeds: Seed data for consistent test environments
- schemas: JSON schemas for validation
- compliance: GDPR-compliant data management utilities
"""

__version__ = "1.0.0"
__all__ = [
    "APIRequestFactory",
    "ArtifactFactory",
    "AuthTokenFactory",
    "RateLimitFactory",
    "TestDataGenerator",
    "ComplianceManager",
]
