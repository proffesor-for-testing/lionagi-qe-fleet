"""
State Encoder for Q-Learning

Converts task context into discrete state representations for Q-table lookup.
Uses SHA-256 hashing for efficient state space management and feature extraction
for generalization across similar states.
"""

import hashlib
import json
from typing import Dict, Any, Tuple, Optional
from enum import Enum


class ComplexityBucket(str, Enum):
    """Complexity buckets for state generalization"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class StateEncoder:
    """
    Encodes task context into discrete state representations.

    Supports 18 different agent types with agent-specific feature extraction.
    Uses bucketing for generalization and SHA-256 hashing for fast lookups.
    """

    # Agent type definitions (18 agents)
    AGENT_TYPES = [
        "test-generator", "test-executor", "coverage-analyzer",
        "quality-gate", "quality-analyzer", "performance-tester",
        "security-scanner", "requirements-validator", "production-intelligence",
        "fleet-commander", "deployment-readiness", "regression-risk-analyzer",
        "test-data-architect", "api-contract-validator", "flaky-test-hunter",
        "visual-tester", "chaos-engineer", "code-complexity"
    ]

    def __init__(self, agent_type: str):
        """
        Initialize state encoder for specific agent type.

        Args:
            agent_type: Type of agent (must be in AGENT_TYPES)

        Raises:
            ValueError: If agent_type is not recognized
        """
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Must be one of: {', '.join(self.AGENT_TYPES)}"
            )

        self.agent_type = agent_type

    def encode_state(self, task_context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Encode task context into state hash and state data.

        Args:
            task_context: Raw task context from execution

        Returns:
            Tuple of (state_hash, state_data) where:
            - state_hash: SHA-256 hash for fast Q-table lookup
            - state_data: Full state representation for debugging
        """
        # Extract features based on agent type
        features = self._extract_features(task_context)

        # Create discrete state tuple
        state_tuple = self._create_state_tuple(features)

        # Generate hash
        state_hash = self._hash_state(state_tuple)

        # Create state data
        state_data = {
            "agent_type": self.agent_type,
            "features": features,
            "state_tuple": state_tuple,
            "raw_context": task_context
        }

        return state_hash, state_data

    def _extract_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant features from task context.

        Different agent types extract different features.

        Args:
            context: Task context dictionary

        Returns:
            Dictionary of extracted features
        """
        # Common features across all agents
        features = {
            "task_type": context.get("task_type", "unknown"),
            "complexity": self._determine_complexity(context),
        }

        # Agent-specific feature extraction
        if self.agent_type == "test-generator":
            features.update(self._extract_test_generator_features(context))
        elif self.agent_type == "test-executor":
            features.update(self._extract_test_executor_features(context))
        elif self.agent_type == "coverage-analyzer":
            features.update(self._extract_coverage_analyzer_features(context))
        elif self.agent_type == "quality-gate":
            features.update(self._extract_quality_gate_features(context))
        elif self.agent_type == "performance-tester":
            features.update(self._extract_performance_tester_features(context))
        elif self.agent_type == "security-scanner":
            features.update(self._extract_security_scanner_features(context))
        elif self.agent_type == "flaky-test-hunter":
            features.update(self._extract_flaky_test_hunter_features(context))
        else:
            # Generic features for other agent types
            features.update(self._extract_generic_features(context))

        return features

    def _determine_complexity(self, context: Dict[str, Any]) -> str:
        """
        Determine task complexity bucket.

        Args:
            context: Task context

        Returns:
            Complexity bucket (simple/moderate/complex)
        """
        # Use multiple signals to determine complexity
        score = 0

        # File/code size indicators
        lines_of_code = context.get("lines_of_code", 0)
        if lines_of_code > 500:
            score += 2
        elif lines_of_code > 100:
            score += 1

        # Cyclomatic complexity
        cyclomatic = context.get("cyclomatic_complexity", 0)
        if cyclomatic > 20:
            score += 2
        elif cyclomatic > 10:
            score += 1

        # Number of dependencies
        num_deps = context.get("num_dependencies", 0)
        if num_deps > 10:
            score += 1

        # Test count
        num_tests = context.get("num_tests", 0)
        if num_tests > 100:
            score += 1

        # Map score to bucket
        if score >= 4:
            return ComplexityBucket.COMPLEX
        elif score >= 2:
            return ComplexityBucket.MODERATE
        else:
            return ComplexityBucket.SIMPLE

    def _extract_test_generator_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for test generator agent"""
        return {
            "coverage_gap": min(int(context.get("coverage_gap", 0) // 10), 10),
            "framework": context.get("framework", "unknown"),
            "test_type": context.get("test_type", "unit"),
            "num_functions": min(context.get("num_functions", 0) // 5, 20),
        }

    def _extract_test_executor_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for test executor agent"""
        return {
            "num_tests_bucket": min(context.get("num_tests", 0) // 100, 100),
            "parallel_workers": min(context.get("parallel_workers", 1), 16),
            "ci_environment": context.get("ci_environment", False),
        }

    def _extract_coverage_analyzer_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for coverage analyzer agent"""
        return {
            "line_coverage_bucket": int(context.get("line_coverage", 0) // 10),
            "branch_coverage_bucket": int(context.get("branch_coverage", 0) // 10),
            "critical_paths_uncovered": min(
                context.get("critical_paths_uncovered", 0) // 5, 20
            ),
        }

    def _extract_quality_gate_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for quality gate agent"""
        return {
            "test_pass_rate_bucket": int(context.get("test_pass_rate", 100) // 10),
            "has_blockers": context.get("blocker_issues", 0) > 0,
            "is_release_build": context.get("is_release_build", False),
        }

    def _extract_performance_tester_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for performance tester agent"""
        return {
            "target_rps_bucket": min(context.get("target_rps", 0) // 1000, 100),
            "test_type": context.get("test_type", "load"),
            "latency_bucket": int(context.get("latency_p95_ms", 0) // 100),
        }

    def _extract_security_scanner_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for security scanner agent"""
        return {
            "scan_type": context.get("scan_type", "SAST"),
            "has_critical_vulns": context.get("critical_vulns", 0) > 0,
            "compliance_standard": context.get("compliance_standard", "OWASP"),
        }

    def _extract_flaky_test_hunter_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for flaky test hunter agent"""
        return {
            "failure_rate_bucket": int(context.get("test_failure_rate", 0) * 10),
            "failure_pattern": context.get("failure_pattern", "unknown"),
            "has_external_deps": (
                context.get("depends_on_network", False) or
                context.get("depends_on_external_service", False)
            ),
        }

    def _extract_generic_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract generic features for other agent types"""
        return {
            "scope": context.get("scope", "module"),
            "environment": context.get("environment", "development"),
        }

    def _create_state_tuple(self, features: Dict[str, Any]) -> Tuple:
        """
        Create hashable state tuple from features.

        Args:
            features: Extracted features

        Returns:
            Tuple of feature values (hashable)
        """
        # Sort keys for consistency
        sorted_keys = sorted(features.keys())

        # Create tuple of values
        values = []
        for key in sorted_keys:
            value = features[key]
            # Convert unhashable types to strings
            if isinstance(value, (dict, list)):
                value = json.dumps(value, sort_keys=True)
            values.append(value)

        return tuple(values)

    def _hash_state(self, state_tuple: Tuple) -> str:
        """
        Generate SHA-256 hash of state tuple.

        Args:
            state_tuple: State as tuple

        Returns:
            64-character hex hash
        """
        # Convert tuple to string
        state_str = json.dumps(state_tuple, sort_keys=True)

        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(state_str.encode('utf-8'))

        # Return hex digest (64 characters)
        return hash_obj.hexdigest()

    def decode_state(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode state data back to human-readable features.

        Args:
            state_data: Encoded state data

        Returns:
            Dictionary of decoded features
        """
        return state_data.get("features", {})
