"""
Reward Calculator for Q-Learning

Calculates multi-component rewards for agent actions based on:
- Coverage improvement
- Quality score changes
- Time efficiency
- Pattern reuse

Uses weighted sum to balance different objectives.
"""

from typing import Dict, Any, Optional
import logging


class RewardCalculator:
    """
    Calculates rewards for QE agent actions.

    Implements multi-objective reward function with configurable weights:
    - Coverage gain (30%): Rewards coverage improvements
    - Quality improvement (25%): Rewards quality score increases
    - Time efficiency (20%): Rewards faster execution
    - Pattern reuse (15%): Rewards successful pattern application
    - Cost efficiency (10%): Rewards lower costs

    Penalties:
    - Task failure: -50 points
    - Timeout: -25 points
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reward calculator.

        Args:
            config: Optional configuration dictionary with reward weights
        """
        self.logger = logging.getLogger("lionagi_qe.learning.reward")

        # Default weights
        self.weights = {
            "coverage_gain": 0.30,
            "quality_improvement": 0.25,
            "time_efficiency": 0.20,
            "pattern_reuse": 0.15,
            "cost_efficiency": 0.10,
        }

        # Override with config if provided
        if config and "weights" in config:
            self.weights.update(config["weights"])

        # Thresholds and targets
        self.target_coverage = config.get("target_coverage", 80.0) if config else 80.0
        self.target_quality = config.get("target_quality", 75.0) if config else 75.0
        self.expected_time_seconds = config.get("expected_time", 60.0) if config else 60.0

    def calculate_reward(
        self,
        state_before: Dict[str, Any],
        action: str,
        state_after: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate composite reward for agent action.

        Args:
            state_before: State before action
            action: Action taken
            state_after: State after action
            metadata: Execution metadata (time, cost, success, etc.)

        Returns:
            Total reward (can be negative for poor performance)
        """
        # Check for immediate failure
        if metadata.get("task_failed", False):
            self.logger.warning(
                f"Task failed for action '{action}'. Applying failure penalty."
            )
            return -50.0

        # Calculate individual reward components
        coverage_reward = self._calculate_coverage_reward(
            state_before, state_after
        )

        quality_reward = self._calculate_quality_reward(
            state_before, state_after
        )

        time_reward = self._calculate_time_reward(metadata)

        pattern_reward = self._calculate_pattern_reward(metadata)

        cost_reward = self._calculate_cost_reward(metadata)

        # Weighted sum
        total_reward = (
            self.weights["coverage_gain"] * coverage_reward +
            self.weights["quality_improvement"] * quality_reward +
            self.weights["time_efficiency"] * time_reward +
            self.weights["pattern_reuse"] * pattern_reward +
            self.weights["cost_efficiency"] * cost_reward
        )

        # Bonus for exceeding expectations
        coverage_after = state_after.get("coverage_percentage", 0)
        if coverage_after >= 90:
            total_reward += 20.0
            self.logger.info("Coverage bonus: +20 points (90%+ coverage)")

        quality_after = state_after.get("quality_score", 0)
        if quality_after >= 90:
            total_reward += 15.0
            self.logger.info("Quality bonus: +15 points (90+ quality score)")

        # Penalty for timeout
        if metadata.get("timed_out", False):
            total_reward -= 25.0
            self.logger.warning("Timeout penalty: -25 points")

        self.logger.debug(
            f"Reward breakdown - Coverage: {coverage_reward:.2f}, "
            f"Quality: {quality_reward:.2f}, Time: {time_reward:.2f}, "
            f"Pattern: {pattern_reward:.2f}, Cost: {cost_reward:.2f}, "
            f"Total: {total_reward:.2f}"
        )

        return total_reward

    def _calculate_coverage_reward(
        self,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any]
    ) -> float:
        """
        Calculate reward for coverage improvement.

        Returns:
            Coverage reward (0-100 points, 1% gain = 10 points)
        """
        coverage_before = state_before.get("coverage_percentage", 0.0)
        coverage_after = state_after.get("coverage_percentage", 0.0)

        coverage_gain = coverage_after - coverage_before

        # Scale: 1% coverage gain = 10 points
        reward = coverage_gain * 10.0

        # Cap at 100 points
        return min(reward, 100.0)

    def _calculate_quality_reward(
        self,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any]
    ) -> float:
        """
        Calculate reward for quality improvement.

        Returns:
            Quality reward (0-100 points)
        """
        quality_before = state_before.get("quality_score", 50.0)
        quality_after = state_after.get("quality_score", 50.0)

        quality_gain = quality_after - quality_before

        # Scale: 1 point quality gain = 2 reward points
        reward = quality_gain * 2.0

        # Also reward for bugs found
        bugs_found = state_after.get("bugs_found", 0)
        critical_bugs = state_after.get("critical_bugs", 0)

        reward += bugs_found * 5.0
        reward += critical_bugs * 20.0

        # Cap at 100 points
        return min(reward, 100.0)

    def _calculate_time_reward(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate reward for time efficiency.

        Returns:
            Time reward (-50 to +50 points)
        """
        actual_time = metadata.get("actual_time_seconds", self.expected_time_seconds)
        expected_time = metadata.get("expected_time_seconds", self.expected_time_seconds)

        if actual_time <= 0:
            return 0.0

        # Calculate time ratio (expected / actual)
        time_ratio = expected_time / actual_time

        # Faster = positive reward, slower = negative reward
        # 50% faster = +25 points, 50% slower = -25 points
        reward = (time_ratio - 1.0) * 50.0

        # Cap between -50 and +50
        return max(-50.0, min(reward, 50.0))

    def _calculate_pattern_reward(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate reward for pattern reuse.

        Returns:
            Pattern reward (0-40 points)
        """
        pattern_reused = metadata.get("pattern_reused", False)
        pattern_success = metadata.get("pattern_success", False)

        if pattern_reused and pattern_success:
            # Successful pattern reuse
            return 40.0
        elif pattern_reused and not pattern_success:
            # Pattern was tried but failed
            return -10.0
        else:
            # No pattern reuse (neutral)
            return 0.0

    def _calculate_cost_reward(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate reward for cost efficiency.

        Returns:
            Cost reward (-25 to +50 points)
        """
        estimated_cost = metadata.get("estimated_cost", 0.01)
        actual_cost = metadata.get("actual_cost", 0.01)

        if actual_cost <= 0:
            return 0.0

        # Calculate cost ratio (estimated / actual)
        cost_ratio = estimated_cost / actual_cost

        # Under budget = positive reward, over budget = negative reward
        reward = (cost_ratio - 1.0) * 50.0

        # Cap between -25 and +50
        return max(-25.0, min(reward, 50.0))

    def calculate_agent_specific_reward(
        self,
        agent_type: str,
        state_before: Dict[str, Any],
        action: str,
        state_after: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate agent-specific reward adjustments.

        Args:
            agent_type: Type of agent
            state_before: State before action
            action: Action taken
            state_after: State after action
            metadata: Execution metadata

        Returns:
            Additional reward (positive or negative)
        """
        # Base reward
        base_reward = self.calculate_reward(
            state_before, action, state_after, metadata
        )

        # Agent-specific adjustments
        if agent_type == "test-generator":
            return base_reward + self._test_generator_adjustment(metadata)
        elif agent_type == "flaky-test-hunter":
            return base_reward + self._flaky_hunter_adjustment(metadata)
        elif agent_type == "performance-tester":
            return base_reward + self._performance_tester_adjustment(metadata)
        else:
            return base_reward

    def _test_generator_adjustment(self, metadata: Dict[str, Any]) -> float:
        """Reward adjustment for test generator agent"""
        adjustment = 0.0

        # Reward edge case coverage
        edge_cases_covered = metadata.get("edge_cases_covered", 0)
        adjustment += edge_cases_covered * 5.0

        # Penalty for generating too many or too few tests
        tests_generated = metadata.get("tests_generated", 0)
        optimal_test_count = metadata.get("optimal_test_count", 10)

        deviation = abs(tests_generated - optimal_test_count)
        adjustment -= deviation * 2.0

        return adjustment

    def _flaky_hunter_adjustment(self, metadata: Dict[str, Any]) -> float:
        """Reward adjustment for flaky test hunter agent"""
        # Use F1-score based reward
        true_positives = metadata.get("true_positives", 0)
        false_positives = metadata.get("false_positives", 0)
        false_negatives = metadata.get("false_negatives", 0)

        # Calculate precision and recall
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )

        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )

        # F1 score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0

        # Convert to reward (0-100)
        reward = f1_score * 100.0

        # Penalties
        reward -= false_negatives * 20.0  # Missed flaky tests are costly
        reward -= false_positives * 5.0   # False alarms are less costly

        return reward

    def _performance_tester_adjustment(self, metadata: Dict[str, Any]) -> float:
        """Reward adjustment for performance tester agent"""
        adjustment = 0.0

        # Reward if baseline performance was met or exceeded
        baseline_met = metadata.get("baseline_met", False)
        if baseline_met:
            adjustment += 30.0

        # Reward for finding performance regressions
        regressions_found = metadata.get("regressions_found", 0)
        adjustment += regressions_found * 15.0

        return adjustment
