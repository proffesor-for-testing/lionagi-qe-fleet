"""Unit tests for RewardCalculator - Reward computation for Q-Learning

Tests cover:
- Coverage reward calculation
- Quality reward calculation
- Time reward calculation (inverted)
- Pattern reuse bonus
- Weighted sum of all components
- Failure penalty
- Edge cases (negative values, zero coverage, extreme values)
"""

import pytest
from typing import Dict, Any
from lionagi_qe.learning.reward_calculator import RewardCalculator


class TestRewardCalculator:
    """Test RewardCalculator initialization and basic functionality"""

    def test_init(self):
        """Test calculator initialization"""
        calculator = RewardCalculator()

        assert calculator is not None
        assert hasattr(calculator, 'calculate')
        assert hasattr(calculator, 'coverage_reward')
        assert hasattr(calculator, 'quality_reward')

    def test_init_with_custom_weights(self, reward_weights):
        """Test calculator with custom weights"""
        calculator = RewardCalculator(weights=reward_weights)

        assert calculator.weights == reward_weights
        assert calculator.weights["coverage"] == 0.30
        assert calculator.weights["quality"] == 0.25

    def test_default_weights(self):
        """Test default weight configuration"""
        calculator = RewardCalculator()

        # Should have weights for all components
        assert "coverage" in calculator.weights
        assert "quality" in calculator.weights
        assert "time" in calculator.weights

        # Weights should sum to 1.0
        assert abs(sum(calculator.weights.values()) - 1.0) < 0.01


class TestCoverageReward:
    """Test coverage-based reward calculation"""

    def test_coverage_reward_improvement(self):
        """Test reward for coverage improvement"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(
            current_coverage=0.8,
            previous_coverage=0.6
        )

        # Positive reward for improvement
        assert reward > 0

    def test_coverage_reward_no_change(self):
        """Test reward when coverage doesn't change"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(
            current_coverage=0.7,
            previous_coverage=0.7
        )

        # Zero or minimal reward
        assert reward == 0

    def test_coverage_reward_decrease(self):
        """Test penalty when coverage decreases"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(
            current_coverage=0.5,
            previous_coverage=0.7
        )

        # Negative reward (penalty)
        assert reward < 0

    def test_coverage_reward_large_improvement(self):
        """Test reward scales with improvement magnitude"""
        calculator = RewardCalculator()

        small_improvement = calculator.coverage_reward(0.65, 0.6)
        large_improvement = calculator.coverage_reward(0.8, 0.6)

        # Larger improvement should give larger reward
        assert large_improvement > small_improvement

    def test_coverage_reward_full_coverage(self):
        """Test achieving full coverage"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(1.0, 0.9)

        # Bonus for reaching 100%
        assert reward > 0


class TestQualityReward:
    """Test quality-based reward calculation"""

    def test_quality_reward_high_quality(self):
        """Test reward for high quality tests"""
        calculator = RewardCalculator()

        reward = calculator.quality_reward(
            bugs_found=5,
            false_positives=1,
            edge_cases_covered=10
        )

        # High quality should give high reward
        assert reward > 0

    def test_quality_reward_no_bugs(self):
        """Test reward when no bugs found"""
        calculator = RewardCalculator()

        reward = calculator.quality_reward(
            bugs_found=0,
            false_positives=0,
            edge_cases_covered=5
        )

        # Minimal reward for edge cases only
        assert reward >= 0

    def test_quality_reward_many_false_positives(self):
        """Test penalty for many false positives"""
        calculator = RewardCalculator()

        reward = calculator.quality_reward(
            bugs_found=3,
            false_positives=10,
            edge_cases_covered=5
        )

        # High false positives should reduce reward
        assert reward < calculator.quality_reward(3, 1, 5)

    def test_quality_reward_edge_cases(self):
        """Test reward increases with edge cases covered"""
        calculator = RewardCalculator()

        few_edges = calculator.quality_reward(2, 1, 3)
        many_edges = calculator.quality_reward(2, 1, 15)

        # More edge cases should give higher reward
        assert many_edges > few_edges

    def test_quality_reward_precision(self):
        """Test quality reward considers precision (bugs/total)"""
        calculator = RewardCalculator()

        # High precision (few false positives)
        high_precision = calculator.quality_reward(5, 1, 10)

        # Low precision (many false positives)
        low_precision = calculator.quality_reward(5, 10, 10)

        assert high_precision > low_precision


class TestTimeReward:
    """Test time-based reward calculation (inverted - faster is better)"""

    def test_time_reward_fast_execution(self):
        """Test reward for fast execution"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(execution_time=1.0)

        # Fast execution should give positive reward
        assert reward > 0

    def test_time_reward_slow_execution(self):
        """Test penalty for slow execution"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(execution_time=100.0)

        # Slow execution should give lower/negative reward
        assert reward < calculator.time_reward(1.0)

    def test_time_reward_inverted(self):
        """Test time reward is inverted (faster = higher reward)"""
        calculator = RewardCalculator()

        fast = calculator.time_reward(2.0)
        slow = calculator.time_reward(10.0)

        assert fast > slow

    def test_time_reward_very_fast(self):
        """Test reward for very fast execution"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(0.1)

        # Very fast should give high reward
        assert reward > calculator.time_reward(1.0)

    def test_time_reward_timeout(self):
        """Test penalty for timeout/very slow execution"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(300.0)  # 5 minutes

        # Should be penalized
        assert reward < 0


class TestPatternBonus:
    """Test pattern reuse bonus calculation"""

    def test_pattern_bonus_reused(self):
        """Test bonus for reusing learned patterns"""
        calculator = RewardCalculator()

        reward = calculator.pattern_bonus(patterns_reused=3)

        # Reusing patterns should give bonus
        assert reward > 0

    def test_pattern_bonus_no_reuse(self):
        """Test no bonus when no patterns reused"""
        calculator = RewardCalculator()

        reward = calculator.pattern_bonus(patterns_reused=0)

        assert reward == 0

    def test_pattern_bonus_scales(self):
        """Test bonus scales with number of patterns"""
        calculator = RewardCalculator()

        few_patterns = calculator.pattern_bonus(2)
        many_patterns = calculator.pattern_bonus(10)

        # More patterns should give higher bonus
        assert many_patterns > few_patterns

    def test_pattern_bonus_diminishing_returns(self):
        """Test bonus has diminishing returns"""
        calculator = RewardCalculator()

        bonus_10 = calculator.pattern_bonus(10)
        bonus_20 = calculator.pattern_bonus(20)
        bonus_30 = calculator.pattern_bonus(30)

        # Incremental bonus should decrease
        diff_10_20 = bonus_20 - bonus_10
        diff_20_30 = bonus_30 - bonus_20

        assert diff_20_30 < diff_10_20


class TestCostReward:
    """Test cost efficiency reward"""

    def test_cost_reward_efficient(self):
        """Test reward for cost-efficient execution"""
        calculator = RewardCalculator()

        reward = calculator.cost_reward(cost=0.05)

        # Low cost should give positive reward
        assert reward > 0

    def test_cost_reward_expensive(self):
        """Test penalty for expensive execution"""
        calculator = RewardCalculator()

        reward = calculator.cost_reward(cost=5.0)

        # High cost should give lower reward
        assert reward < calculator.cost_reward(0.05)

    def test_cost_reward_free(self):
        """Test maximum reward for free execution"""
        calculator = RewardCalculator()

        reward = calculator.cost_reward(cost=0.0)

        # Free should give maximum reward
        assert reward > calculator.cost_reward(0.01)


class TestWeightedReward:
    """Test weighted sum of all reward components"""

    def test_calculate_full_reward(self):
        """Test calculating full weighted reward"""
        calculator = RewardCalculator()

        result = {
            "coverage": 0.85,
            "previous_coverage": 0.70,
            "bugs_found": 5,
            "false_positives": 1,
            "edge_cases_covered": 10,
            "execution_time": 3.5,
            "patterns_reused": 2,
            "cost": 0.10
        }

        reward = calculator.calculate(result)

        # Should return positive reward for good result
        assert reward > 0

    def test_calculate_applies_weights(self):
        """Test calculate applies correct weights to components"""
        weights = {
            "coverage": 0.5,
            "quality": 0.3,
            "time": 0.2
        }
        calculator = RewardCalculator(weights=weights)

        result = {
            "coverage": 0.8,
            "previous_coverage": 0.6,
            "bugs_found": 3,
            "execution_time": 2.0
        }

        reward = calculator.calculate(result)

        # Should combine all components
        assert isinstance(reward, float)

    def test_calculate_missing_fields(self):
        """Test calculate handles missing result fields"""
        calculator = RewardCalculator()

        result = {
            "coverage": 0.8,
            "previous_coverage": 0.7
            # Missing other fields
        }

        reward = calculator.calculate(result)

        # Should use defaults for missing fields
        assert isinstance(reward, float)

    def test_calculate_excellent_result(self):
        """Test reward for excellent test result"""
        calculator = RewardCalculator()

        excellent = {
            "coverage": 1.0,
            "previous_coverage": 0.5,
            "bugs_found": 10,
            "false_positives": 0,
            "edge_cases_covered": 20,
            "execution_time": 1.0,
            "patterns_reused": 5,
            "cost": 0.01
        }

        reward = calculator.calculate(excellent)

        # Should give high reward
        assert reward > 10.0

    def test_calculate_poor_result(self):
        """Test penalty for poor test result"""
        calculator = RewardCalculator()

        poor = {
            "coverage": 0.3,
            "previous_coverage": 0.5,  # Decreased
            "bugs_found": 0,
            "false_positives": 10,
            "edge_cases_covered": 1,
            "execution_time": 100.0,
            "patterns_reused": 0,
            "cost": 5.0
        }

        reward = calculator.calculate(poor)

        # Should give negative/low reward
        assert reward < 0


class TestFailurePenalty:
    """Test penalty for task failures"""

    def test_failure_penalty(self):
        """Test penalty for task failure"""
        calculator = RewardCalculator()

        penalty = calculator.failure_penalty()

        # Should return negative value
        assert penalty < 0

    def test_failure_penalty_magnitude(self):
        """Test failure penalty is significant"""
        calculator = RewardCalculator()

        penalty = calculator.failure_penalty()

        # Should be substantial penalty
        assert penalty < -5.0

    def test_calculate_with_failure(self):
        """Test calculate returns penalty for failure"""
        calculator = RewardCalculator()

        result = {"failed": True}

        reward = calculator.calculate(result)

        # Should return failure penalty
        assert reward < 0
        assert reward == calculator.failure_penalty()


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_coverage_reward_negative_coverage(self):
        """Test handling negative coverage (invalid)"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(-0.1, 0.5)

        # Should handle gracefully (treat as 0 or error)
        assert isinstance(reward, (int, float))

    def test_coverage_reward_over_100(self):
        """Test handling coverage > 1.0 (invalid)"""
        calculator = RewardCalculator()

        reward = calculator.coverage_reward(1.5, 0.8)

        # Should handle gracefully (clamp to 1.0)
        assert isinstance(reward, (int, float))

    def test_quality_reward_negative_bugs(self):
        """Test handling negative bug count (invalid)"""
        calculator = RewardCalculator()

        reward = calculator.quality_reward(-5, 1, 10)

        # Should handle gracefully
        assert isinstance(reward, (int, float))

    def test_time_reward_zero_time(self):
        """Test handling zero execution time"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(0.0)

        # Should handle gracefully (maximum reward or small value)
        assert isinstance(reward, (int, float))
        assert reward >= 0

    def test_time_reward_negative_time(self):
        """Test handling negative time (invalid)"""
        calculator = RewardCalculator()

        reward = calculator.time_reward(-1.0)

        # Should handle gracefully
        assert isinstance(reward, (int, float))

    def test_pattern_bonus_negative_patterns(self):
        """Test handling negative pattern count (invalid)"""
        calculator = RewardCalculator()

        reward = calculator.pattern_bonus(-3)

        # Should handle gracefully (treat as 0)
        assert reward == 0

    def test_calculate_empty_result(self):
        """Test calculate with empty result dict"""
        calculator = RewardCalculator()

        reward = calculator.calculate({})

        # Should use all defaults
        assert isinstance(reward, float)

    def test_calculate_none_values(self):
        """Test calculate with None values"""
        calculator = RewardCalculator()

        result = {
            "coverage": None,
            "bugs_found": None,
            "execution_time": None
        }

        reward = calculator.calculate(result)

        # Should handle None gracefully
        assert isinstance(reward, float)

    def test_reward_ranges(self):
        """Test reward values are in reasonable ranges"""
        calculator = RewardCalculator()

        # Good result
        good_result = {
            "coverage": 0.9,
            "previous_coverage": 0.7,
            "bugs_found": 5,
            "execution_time": 2.0
        }

        reward = calculator.calculate(good_result)

        # Should be in reasonable range (e.g., -100 to 100)
        assert -100 < reward < 100


class TestRewardNormalization:
    """Test reward normalization and scaling"""

    def test_rewards_comparable(self):
        """Test rewards from different components are comparable"""
        calculator = RewardCalculator()

        # Different result types
        coverage_result = {"coverage": 0.9, "previous_coverage": 0.7}
        quality_result = {"bugs_found": 5, "edge_cases_covered": 10}
        time_result = {"execution_time": 2.0}

        coverage_reward = calculator.calculate(coverage_result)
        quality_reward = calculator.calculate(quality_result)
        time_reward = calculator.calculate(time_result)

        # All should be in similar magnitude range
        all_rewards = [coverage_reward, quality_reward, time_reward]
        assert max(all_rewards) < 100
        assert min(all_rewards) > -100

    def test_reward_scaling_consistent(self):
        """Test reward scaling is consistent across components"""
        calculator = RewardCalculator()

        # Small changes should give small rewards
        small_change = {
            "coverage": 0.71,
            "previous_coverage": 0.70
        }

        # Large changes should give large rewards
        large_change = {
            "coverage": 0.95,
            "previous_coverage": 0.50
        }

        small_reward = calculator.calculate(small_change)
        large_reward = calculator.calculate(large_change)

        # Large change should give significantly larger reward
        assert large_reward > small_reward * 5
