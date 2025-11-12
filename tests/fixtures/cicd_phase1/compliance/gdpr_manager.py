"""
GDPR Compliance Manager

Ensures test data complies with GDPR and other data protection regulations.
"""

import hashlib
import re
import secrets
from typing import Any, Dict, List, Optional, Set

from faker import Faker

fake = Faker()


class GDPRComplianceManager:
    """Manages GDPR compliance for test data"""

    # PII fields that must be anonymized or removed
    PII_FIELDS = {
        "email",
        "name",
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "phone_number",
        "address",
        "street_address",
        "city",
        "postal_code",
        "zip_code",
        "ssn",
        "social_security_number",
        "credit_card",
        "card_number",
        "ip_address",
        "mac_address",
        "passport_number",
        "driver_license",
        "date_of_birth",
        "birthdate",
    }

    # Patterns to detect PII in values
    PII_PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
        "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    }

    def __init__(self, salt: Optional[str] = None):
        self.salt = salt or secrets.token_hex(16)

    def scan_for_pii(self, data: Any) -> List[str]:
        """Scan data structure for potential PII"""
        pii_found = []

        def scan_recursive(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    # Check if key name suggests PII
                    if key.lower() in self.PII_FIELDS:
                        pii_found.append({
                            "path": current_path,
                            "field": key,
                            "reason": "Field name indicates PII",
                        })

                    # Recursively scan nested structures
                    scan_recursive(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan_recursive(item, f"{path}[{i}]")

            elif isinstance(obj, str):
                # Check if value matches PII patterns
                for pii_type, pattern in self.PII_PATTERNS.items():
                    if pattern.search(obj):
                        pii_found.append({
                            "path": path,
                            "type": pii_type,
                            "reason": f"Value matches {pii_type} pattern",
                        })

        scan_recursive(data)
        return pii_found

    def anonymize_data(
        self,
        data: Any,
        strategy: str = "hash",
        preserve_format: bool = True,
    ) -> Any:
        """Anonymize PII in data structure"""

        def anonymize_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    key: (
                        self._anonymize_value(value, key, strategy, preserve_format)
                        if key.lower() in self.PII_FIELDS
                        else anonymize_recursive(value)
                    )
                    for key, value in obj.items()
                }

            elif isinstance(obj, list):
                return [anonymize_recursive(item) for item in obj]

            elif isinstance(obj, str):
                # Check if string contains PII patterns
                result = obj
                for pii_type, pattern in self.PII_PATTERNS.items():
                    if pattern.search(result):
                        result = pattern.sub(
                            lambda m: self._anonymize_value(m.group(), pii_type, strategy, preserve_format),
                            result,
                        )
                return result

            else:
                return obj

        return anonymize_recursive(data)

    def _anonymize_value(
        self,
        value: Any,
        field_name: str,
        strategy: str,
        preserve_format: bool,
    ) -> Any:
        """Anonymize a single value"""
        if value is None:
            return None

        strategies = {
            "hash": lambda v: self._hash_value(v),
            "fake": lambda v: self._fake_value(v, field_name, preserve_format),
            "mask": lambda v: self._mask_value(v, preserve_format),
            "remove": lambda v: None,
            "generic": lambda v: self._generic_value(field_name),
        }

        anonymizer = strategies.get(strategy, strategies["hash"])
        return anonymizer(value)

    def _hash_value(self, value: Any) -> str:
        """Hash value with salt"""
        value_str = str(value)
        salted = f"{value_str}{self.salt}"
        return hashlib.sha256(salted.encode()).hexdigest()[:16]

    def _fake_value(self, value: Any, field_name: str, preserve_format: bool) -> Any:
        """Generate fake value"""
        field_lower = field_name.lower()

        generators = {
            "email": fake.email,
            "name": fake.name,
            "first_name": fake.first_name,
            "last_name": fake.last_name,
            "phone": fake.phone_number,
            "phone_number": fake.phone_number,
            "address": fake.address,
            "street_address": fake.street_address,
            "city": fake.city,
            "postal_code": fake.postcode,
            "zip_code": fake.zipcode,
            "ssn": lambda: fake.ssn() if hasattr(fake, "ssn") else fake.numerify("###-##-####"),
            "credit_card": fake.credit_card_number,
            "ip_address": fake.ipv4,
        }

        generator = generators.get(field_lower, lambda: fake.word())
        return generator()

    def _mask_value(self, value: Any, preserve_format: bool) -> str:
        """Mask value while preserving format"""
        value_str = str(value)

        if not preserve_format:
            return "*" * len(value_str)

        # Preserve first and last character, mask middle
        if len(value_str) <= 2:
            return "*" * len(value_str)

        return value_str[0] + "*" * (len(value_str) - 2) + value_str[-1]

    def _generic_value(self, field_name: str) -> str:
        """Generate generic placeholder"""
        return f"<{field_name.upper()}_REDACTED>"

    def generate_compliance_report(self, data: Any) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        pii_findings = self.scan_for_pii(data)

        return {
            "compliant": len(pii_findings) == 0,
            "pii_findings": pii_findings,
            "pii_count": len(pii_findings),
            "recommendations": self._generate_recommendations(pii_findings),
        }

    def _generate_recommendations(self, pii_findings: List[Dict]) -> List[str]:
        """Generate recommendations for addressing PII"""
        if not pii_findings:
            return ["No PII detected. Data is compliant."]

        recommendations = [
            "Anonymize or remove all identified PII fields.",
            "Use synthetic data generators (Faker) instead of real data.",
            "Implement data retention policies to automatically delete test data.",
            "Ensure test environments are isolated from production.",
            "Document data handling procedures in compliance with GDPR.",
        ]

        return recommendations

    def validate_no_production_data(self, data: Any) -> Dict[str, Any]:
        """Validate that data does not contain production data markers"""
        production_markers = [
            "prod",
            "production",
            "live",
            "customer",
            "real",
        ]

        violations = []

        def check_recursive(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    # Check key names
                    if any(marker in key.lower() for marker in production_markers):
                        violations.append({
                            "path": current_path,
                            "reason": "Key name suggests production data",
                        })

                    check_recursive(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")

            elif isinstance(obj, str):
                # Check string values
                if any(marker in obj.lower() for marker in production_markers):
                    violations.append({
                        "path": path,
                        "reason": "Value suggests production data",
                    })

        check_recursive(data)

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "violation_count": len(violations),
        }
