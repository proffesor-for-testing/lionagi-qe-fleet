"""Unit tests for StateEncoder - State representation for Q-Learning

Tests cover:
- State encoding for different task types
- Feature extraction from task context
- Bucketing (complexity, size, coverage)
- State hashing (deterministic)
- All 18 agent types
- Edge cases (missing fields, None values)
"""

import pytest
from typing import Dict, Any
from lionagi_qe.learning.state_encoder import StateEncoder
from lionagi_qe.core.task import QETask


class TestStateEncoder:
    """Test StateEncoder initialization and basic functionality"""

    def test_init(self):
        """Test encoder initialization"""
        encoder = StateEncoder()

        assert encoder is not None
        assert hasattr(encoder, 'encode')
        assert hasattr(encoder, 'extract_features')

    def test_init_with_custom_config(self):
        """Test encoder with custom configuration"""
        config = {
            "complexity_buckets": [5, 10, 20],
            "size_buckets": [50, 200, 500],
            "coverage_buckets": [0.5, 0.7, 0.9]
        }

        encoder = StateEncoder(config=config)

        assert encoder.complexity_buckets == [5, 10, 20]
        assert encoder.size_buckets == [50, 200, 500]
        assert encoder.coverage_buckets == [0.5, 0.7, 0.9]


class TestFeatureExtraction:
    """Test feature extraction from task context"""

    @pytest.mark.asyncio
    async def test_extract_basic_features(self, sample_qe_task):
        """Test extracting basic features from task"""
        encoder = StateEncoder()

        features = encoder.extract_features(sample_qe_task)

        assert "task_type" in features
        assert "framework" in features
        assert "complexity" in features
        assert "coverage" in features
        assert features["task_type"] == "test_generation"
        assert features["framework"] == "pytest"

    @pytest.mark.asyncio
    async def test_extract_with_missing_fields(self):
        """Test feature extraction with missing context fields"""
        encoder = StateEncoder()
        task = QETask(
            task_type="test_execution",
            context={"code": "test"}  # Missing many fields
        )

        features = encoder.extract_features(task)

        # Should use defaults for missing fields
        assert "complexity" in features
        assert "coverage" in features
        assert features["complexity"] == 0  # Default
        assert features["coverage"] == 0.0  # Default

    @pytest.mark.asyncio
    async def test_extract_with_none_values(self):
        """Test feature extraction with None values"""
        encoder = StateEncoder()
        task = QETask(
            task_type="test_generation",
            context={
                "complexity": None,
                "coverage": None,
                "framework": None
            }
        )

        features = encoder.extract_features(task)

        # Should handle None gracefully
        assert features["complexity"] == 0
        assert features["coverage"] == 0.0
        assert features["framework"] == "unknown"

    @pytest.mark.asyncio
    async def test_extract_all_agent_types(self, agent_types):
        """Test feature extraction for all 18 agent types"""
        encoder = StateEncoder()

        for agent_type in agent_types:
            task = QETask(
                task_type=agent_type,
                context={
                    "complexity": 10,
                    "coverage": 0.75,
                    "framework": "pytest"
                }
            )

            features = encoder.extract_features(task)

            assert "task_type" in features
            assert features["task_type"] == agent_type


class TestBucketing:
    """Test bucketing of continuous values"""

    def test_bucket_complexity_low(self):
        """Test complexity bucketing - low"""
        encoder = StateEncoder()

        bucket = encoder.bucket_complexity(3)

        assert bucket == "low"

    def test_bucket_complexity_medium(self):
        """Test complexity bucketing - medium"""
        encoder = StateEncoder()

        bucket = encoder.bucket_complexity(12)

        assert bucket == "medium"

    def test_bucket_complexity_high(self):
        """Test complexity bucketing - high"""
        encoder = StateEncoder()

        bucket = encoder.bucket_complexity(25)

        assert bucket == "high"

    def test_bucket_complexity_very_high(self):
        """Test complexity bucketing - very high"""
        encoder = StateEncoder()

        bucket = encoder.bucket_complexity(50)

        assert bucket == "very_high"

    def test_bucket_size_small(self):
        """Test size bucketing - small"""
        encoder = StateEncoder()

        bucket = encoder.bucket_size(30)

        assert bucket == "small"

    def test_bucket_size_medium(self):
        """Test size bucketing - medium"""
        encoder = StateEncoder()

        bucket = encoder.bucket_size(150)

        assert bucket == "medium"

    def test_bucket_size_large(self):
        """Test size bucketing - large"""
        encoder = StateEncoder()

        bucket = encoder.bucket_size(350)

        assert bucket == "large"

    def test_bucket_size_very_large(self):
        """Test size bucketing - very large"""
        encoder = StateEncoder()

        bucket = encoder.bucket_size(700)

        assert bucket == "very_large"

    def test_bucket_coverage_low(self):
        """Test coverage bucketing - low"""
        encoder = StateEncoder()

        bucket = encoder.bucket_coverage(0.3)

        assert bucket == "low"

    def test_bucket_coverage_medium(self):
        """Test coverage bucketing - medium"""
        encoder = StateEncoder()

        bucket = encoder.bucket_coverage(0.6)

        assert bucket == "medium"

    def test_bucket_coverage_high(self):
        """Test coverage bucketing - high"""
        encoder = StateEncoder()

        bucket = encoder.bucket_coverage(0.8)

        assert bucket == "high"

    def test_bucket_coverage_full(self):
        """Test coverage bucketing - full"""
        encoder = StateEncoder()

        bucket = encoder.bucket_coverage(1.0)

        assert bucket == "full"

    def test_bucket_edge_values(self):
        """Test bucketing at exact boundary values"""
        encoder = StateEncoder()

        # Complexity boundaries
        assert encoder.bucket_complexity(10) in ["low", "medium"]
        assert encoder.bucket_complexity(20) in ["medium", "high"]

        # Coverage boundaries
        assert encoder.bucket_coverage(0.5) in ["low", "medium"]
        assert encoder.bucket_coverage(0.7) in ["medium", "high"]


class TestStateEncoding:
    """Test full state encoding"""

    @pytest.mark.asyncio
    async def test_encode_basic_task(self, sample_qe_task):
        """Test encoding a basic task"""
        encoder = StateEncoder()

        state = encoder.encode(sample_qe_task)

        assert isinstance(state, str)
        assert len(state) > 0
        assert "test_generation" in state

    @pytest.mark.asyncio
    async def test_encode_deterministic(self, sample_qe_task):
        """Test encoding is deterministic (same input -> same output)"""
        encoder = StateEncoder()

        state1 = encoder.encode(sample_qe_task)
        state2 = encoder.encode(sample_qe_task)

        assert state1 == state2

    @pytest.mark.asyncio
    async def test_encode_different_tasks_different_states(self, sample_task_factory):
        """Test different tasks produce different states"""
        encoder = StateEncoder()

        task1 = sample_task_factory(complexity=5, coverage=0.6)
        task2 = sample_task_factory(complexity=15, coverage=0.8)

        state1 = encoder.encode(task1)
        state2 = encoder.encode(task2)

        assert state1 != state2

    @pytest.mark.asyncio
    async def test_encode_includes_task_type(self):
        """Test encoded state includes task type"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_execution",
            context={"framework": "jest"}
        )

        state = encoder.encode(task)

        assert "test_execution" in state

    @pytest.mark.asyncio
    async def test_encode_includes_bucketed_values(self, sample_task_factory):
        """Test encoded state includes bucketed complexity/coverage"""
        encoder = StateEncoder()

        task = sample_task_factory(complexity=12, coverage=0.75)

        state = encoder.encode(task)

        # Should include bucketed values
        assert "medium" in state or "high" in state

    @pytest.mark.asyncio
    async def test_encode_includes_framework(self):
        """Test encoded state includes framework"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={"framework": "pytest"}
        )

        state = encoder.encode(task)

        assert "pytest" in state

    @pytest.mark.asyncio
    async def test_encode_all_agent_types(self, agent_types):
        """Test encoding for all 18 agent types produces unique states"""
        encoder = StateEncoder()
        states = set()

        for agent_type in agent_types:
            task = QETask(
                task_type=agent_type,
                context={
                    "complexity": 10,
                    "coverage": 0.75,
                    "framework": "pytest"
                }
            )

            state = encoder.encode(task)
            states.add(state)

        # All agent types should produce unique states
        assert len(states) == len(agent_types)


class TestStateHashing:
    """Test state hashing for compact representation"""

    @pytest.mark.asyncio
    async def test_hash_state_deterministic(self):
        """Test state hashing is deterministic"""
        encoder = StateEncoder()

        state_str = "test_gen_complexity_medium_coverage_high_pytest"

        hash1 = encoder.hash_state(state_str)
        hash2 = encoder.hash_state(state_str)

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_hash_state_different_inputs(self):
        """Test different states produce different hashes"""
        encoder = StateEncoder()

        state1 = "test_gen_complexity_low_coverage_medium_pytest"
        state2 = "test_gen_complexity_high_coverage_high_pytest"

        hash1 = encoder.hash_state(state1)
        hash2 = encoder.hash_state(state2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_hash_state_length(self):
        """Test hashed states have reasonable length"""
        encoder = StateEncoder()

        state = "very_long_state_string_with_many_features_and_values"

        hashed = encoder.hash_state(state)

        # SHA256 hash should be 64 characters (hex)
        assert len(hashed) <= 64
        assert len(hashed) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_encode_empty_context(self):
        """Test encoding task with empty context"""
        encoder = StateEncoder()

        task = QETask(task_type="test_generation", context={})

        state = encoder.encode(task)

        # Should still produce valid state with defaults
        assert isinstance(state, str)
        assert len(state) > 0

    @pytest.mark.asyncio
    async def test_encode_very_high_complexity(self):
        """Test encoding with extremely high complexity"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={"complexity": 1000}
        )

        state = encoder.encode(task)

        assert "very_high" in state

    @pytest.mark.asyncio
    async def test_encode_negative_values(self):
        """Test encoding with negative values (invalid input)"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={
                "complexity": -5,
                "coverage": -0.1
            }
        )

        state = encoder.encode(task)

        # Should handle gracefully (treat as 0 or clamp)
        assert isinstance(state, str)

    @pytest.mark.asyncio
    async def test_encode_coverage_over_100(self):
        """Test encoding with coverage > 1.0 (invalid)"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={"coverage": 1.5}
        )

        state = encoder.encode(task)

        # Should handle gracefully (clamp to 1.0)
        assert isinstance(state, str)

    @pytest.mark.asyncio
    async def test_encode_with_special_characters(self):
        """Test encoding with special characters in framework"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={"framework": "pytest-cov@v2.1"}
        )

        state = encoder.encode(task)

        # Should sanitize special characters
        assert isinstance(state, str)
        assert "@" not in state  # Special chars should be removed

    @pytest.mark.asyncio
    async def test_extract_features_type_coercion(self):
        """Test feature extraction with wrong types (strings instead of numbers)"""
        encoder = StateEncoder()

        task = QETask(
            task_type="test_generation",
            context={
                "complexity": "10",  # String instead of int
                "coverage": "0.75"   # String instead of float
            }
        )

        features = encoder.extract_features(task)

        # Should coerce to correct types
        assert isinstance(features["complexity"], int)
        assert isinstance(features["coverage"], float)
