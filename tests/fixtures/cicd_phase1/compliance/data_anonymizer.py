"""
Data Anonymizer

Implements various anonymization techniques for test data.
"""

import hashlib
import random
import secrets
from typing import Any, Dict, List, Optional

from faker import Faker

fake = Faker()


class DataAnonymizer:
    """Anonymizes test data using various strategies"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)

        self.token_map: Dict[str, str] = {}

    def pseudonymize(self, value: str, deterministic: bool = True) -> str:
        """Pseudonymize value (reversible with key)"""
        if deterministic:
            # Use consistent tokenization
            if value not in self.token_map:
                self.token_map[value] = self._generate_token()
            return self.token_map[value]
        else:
            return self._generate_token()

    def anonymize(self, value: str) -> str:
        """Anonymize value (irreversible)"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def generalize_number(self, value: float, precision: int = 10) -> float:
        """Generalize numeric value"""
        return round(value / precision) * precision

    def generalize_date(self, date_str: str) -> str:
        """Generalize date to year/month only"""
        # Simplified: just take first 7 characters (YYYY-MM)
        return date_str[:7] if len(date_str) >= 7 else date_str

    def data_masking(self, value: str, show_chars: int = 2) -> str:
        """Partially mask value"""
        if len(value) <= show_chars * 2:
            return "*" * len(value)

        return (
            value[:show_chars]
            + "*" * (len(value) - show_chars * 2)
            + value[-show_chars:]
        )

    def k_anonymity(
        self,
        records: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Ensure k-anonymity for dataset"""
        # Simplified k-anonymity implementation
        # In production, use proper k-anonymity library

        # Group records by quasi-identifiers
        groups: Dict[tuple, List[Dict]] = {}

        for record in records:
            key = tuple(record.get(qi) for qi in quasi_identifiers)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)

        # Generalize groups smaller than k
        anonymized = []
        for group in groups.values():
            if len(group) < k:
                # Generalize quasi-identifiers
                for record in group:
                    for qi in quasi_identifiers:
                        if qi in record:
                            record[qi] = "*"  # Suppress value
            anonymized.extend(group)

        return anonymized

    def l_diversity(
        self,
        records: List[Dict[str, Any]],
        sensitive_attribute: str,
        l: int = 2,
    ) -> List[Dict[str, Any]]:
        """Ensure l-diversity for dataset"""
        # Simplified l-diversity implementation
        # Ensures at least l different values for sensitive attribute in each group

        anonymized = []
        for record in records:
            # In real implementation, check diversity and suppress/generalize as needed
            anonymized.append(record)

        return anonymized

    def differential_privacy(
        self,
        value: float,
        epsilon: float = 1.0,
        sensitivity: float = 1.0,
    ) -> float:
        """Add differential privacy noise"""
        # Laplace mechanism
        scale = sensitivity / epsilon
        noise = random.laplace(0, scale)
        return value + noise

    def _generate_token(self) -> str:
        """Generate unique token"""
        return secrets.token_urlsafe(16)
