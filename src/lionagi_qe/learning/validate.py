#!/usr/bin/env python3
"""
Validation script for Q-Learning implementation

Checks that all components are properly implemented and can be imported.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_imports():
    """Validate all imports work correctly"""
    logger.info("Validating imports...")

    try:
        from lionagi_qe.learning import (
            QLearningService,
            StateEncoder,
            RewardCalculator,
            DatabaseManager
        )
        logger.info("✓ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def validate_state_encoder():
    """Validate StateEncoder functionality"""
    logger.info("Validating StateEncoder...")

    try:
        from lionagi_qe.learning import StateEncoder

        # Test initialization
        encoder = StateEncoder("test-generator")

        # Test state encoding
        context = {
            "task_type": "test_generation",
            "coverage_percentage": 60.0,
            "quality_score": 70.0,
            "lines_of_code": 500,
            "cyclomatic_complexity": 15,
            "framework": "pytest",
            "test_type": "unit",
            "num_functions": 25
        }

        state_hash, state_data = encoder.encode_state(context)

        # Validate output
        assert isinstance(state_hash, str), "State hash should be string"
        assert len(state_hash) == 64, "State hash should be 64 characters (SHA-256)"
        assert isinstance(state_data, dict), "State data should be dict"
        assert "features" in state_data, "State data should have features"

        logger.info(f"✓ StateEncoder working correctly")
        logger.info(f"  State hash: {state_hash[:16]}...")
        logger.info(f"  Features: {list(state_data['features'].keys())}")

        return True

    except Exception as e:
        logger.error(f"✗ StateEncoder validation failed: {e}")
        return False


def validate_reward_calculator():
    """Validate RewardCalculator functionality"""
    logger.info("Validating RewardCalculator...")

    try:
        from lionagi_qe.learning import RewardCalculator

        # Test initialization
        calc = RewardCalculator()

        # Test reward calculation
        state_before = {
            "coverage_percentage": 60.0,
            "quality_score": 70.0
        }

        state_after = {
            "coverage_percentage": 65.0,
            "quality_score": 75.0,
            "bugs_found": 2
        }

        metadata = {
            "success": True,
            "actual_time_seconds": 30,
            "expected_time_seconds": 40,
            "pattern_reused": True,
            "pattern_success": True
        }

        reward = calc.calculate_reward(
            state_before=state_before,
            action="use_property_based",
            state_after=state_after,
            metadata=metadata
        )

        # Validate output
        assert isinstance(reward, float), "Reward should be float"
        assert reward != 0, "Reward should not be zero with improvements"

        logger.info(f"✓ RewardCalculator working correctly")
        logger.info(f"  Calculated reward: {reward:.2f}")

        # Test failure penalty
        metadata_failed = {"task_failed": True}
        reward_failed = calc.calculate_reward(
            state_before, "test_action", state_after, metadata_failed
        )
        assert reward_failed < 0, "Failed task should have negative reward"
        logger.info(f"  Failure penalty: {reward_failed:.2f}")

        return True

    except Exception as e:
        logger.error(f"✗ RewardCalculator validation failed: {e}")
        return False


def validate_qlearning_service():
    """Validate QLearningService (without DB)"""
    logger.info("Validating QLearningService...")

    try:
        from lionagi_qe.learning import QLearningService

        # Create mock database manager
        class MockDBManager:
            async def connect(self):
                pass

            async def get_q_value(self, agent_type, state_hash, action_hash):
                return None

            async def upsert_q_value(self, *args, **kwargs):
                return 1

            async def update_agent_state(self, *args, **kwargs):
                pass

        # Test initialization
        db_manager = MockDBManager()
        service = QLearningService(
            agent_type="test-generator",
            agent_instance_id="test-gen-1",
            db_manager=db_manager,
            config={
                "learningRate": 0.1,
                "discountFactor": 0.95,
                "explorationRate": 0.2
            }
        )

        # Set action space
        service.set_action_space([
            "action_1",
            "action_2",
            "action_3"
        ])

        # Validate attributes
        assert service.learning_rate == 0.1, "Learning rate should be 0.1"
        assert service.discount_factor == 0.95, "Discount should be 0.95"
        assert service.epsilon == 0.2, "Epsilon should be 0.2"
        assert len(service.action_space) == 3, "Should have 3 actions"

        logger.info(f"✓ QLearningService initialized correctly")
        logger.info(f"  Learning rate: {service.learning_rate}")
        logger.info(f"  Discount factor: {service.discount_factor}")
        logger.info(f"  Epsilon: {service.epsilon}")
        logger.info(f"  Actions: {service.action_space}")

        # Test statistics
        stats = service.get_statistics()
        assert isinstance(stats, dict), "Statistics should be dict"
        assert "total_episodes" in stats, "Stats should have total_episodes"

        logger.info(f"✓ Statistics: {stats}")

        return True

    except Exception as e:
        logger.error(f"✗ QLearningService validation failed: {e}")
        return False


def validate_all_agent_types():
    """Validate all 18 agent types are supported"""
    logger.info("Validating all agent types...")

    try:
        from lionagi_qe.learning import StateEncoder

        expected_agents = [
            "test-generator", "test-executor", "coverage-analyzer",
            "quality-gate", "quality-analyzer", "performance-tester",
            "security-scanner", "requirements-validator", "production-intelligence",
            "fleet-commander", "deployment-readiness", "regression-risk-analyzer",
            "test-data-architect", "api-contract-validator", "flaky-test-hunter",
            "visual-tester", "chaos-engineer", "code-complexity"
        ]

        for agent_type in expected_agents:
            encoder = StateEncoder(agent_type)
            assert encoder.agent_type == agent_type, f"Agent type mismatch: {agent_type}"

        logger.info(f"✓ All {len(expected_agents)} agent types supported")

        # Test invalid agent type
        try:
            StateEncoder("invalid-agent")
            logger.error("✗ Should have raised ValueError for invalid agent")
            return False
        except ValueError:
            logger.info("✓ Invalid agent type properly rejected")

        return True

    except Exception as e:
        logger.error(f"✗ Agent type validation failed: {e}")
        return False


def main():
    """Run all validations"""
    logger.info("=" * 60)
    logger.info("Q-Learning Implementation Validation")
    logger.info("=" * 60)

    results = []

    # Run all validations
    results.append(("Imports", validate_imports()))
    results.append(("StateEncoder", validate_state_encoder()))
    results.append(("RewardCalculator", validate_reward_calculator()))
    results.append(("QLearningService", validate_qlearning_service()))
    results.append(("Agent Types", validate_all_agent_types()))

    # Summary
    logger.info("=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name:20s} {status}")

    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} validations passed")

    if passed == total:
        logger.info("✓ All validations passed!")
        return 0
    else:
        logger.error(f"✗ {total - passed} validation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
