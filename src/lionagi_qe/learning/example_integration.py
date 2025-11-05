"""
Example Integration of Q-Learning with BaseQEAgent

This example shows how to integrate the Q-Learning service with the BaseQEAgent.
This code would be integrated into the base_agent.py file.
"""

import json
import logging
from typing import Dict, Any, Optional

from .qlearner import QLearningService
from .db_manager import DatabaseManager


# Example: How to modify BaseQEAgent to integrate Q-Learning

class QEAgentWithLearning:
    """
    Example showing how to add Q-Learning to an agent.

    This would be integrated into the actual BaseQEAgent class.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        enable_learning: bool = True,
        config_path: str = ".agentic-qe/config/learning.json"
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"lionagi_qe.{agent_id}")

        # Load learning configuration
        with open(config_path, 'r') as f:
            self.learning_config = json.load(f)

        # Initialize Q-Learning components
        if enable_learning and self.learning_config.get("enabled", False):
            self.db_manager = DatabaseManager(
                database_url=self._get_database_url(),
                min_connections=2,
                max_connections=10
            )

            self.q_learning = QLearningService(
                agent_type=agent_type,
                agent_instance_id=agent_id,
                db_manager=self.db_manager,
                config=self.learning_config
            )

            # Set agent-specific action space
            self._setup_action_space()

            self.logger.info(f"Q-Learning enabled for {agent_type}")
        else:
            self.q_learning = None
            self.logger.info(f"Q-Learning disabled for {agent_type}")

    def _get_database_url(self) -> str:
        """Get database URL from environment or config"""
        import os
        return os.getenv(
            "QLEARNING_DB_URL",
            "postgresql://localhost:5432/lionagi_qe_learning"
        )

    def _setup_action_space(self):
        """Setup action space for this agent type"""
        # This would be different for each agent type
        if self.agent_type == "test-generator":
            actions = [
                "use_property_based",
                "use_example_based",
                "use_mutation_testing",
                "prioritize_branches",
                "prioritize_lines",
                "generate_simple",
                "generate_comprehensive",
                "reuse_pattern"
            ]
        elif self.agent_type == "test-executor":
            actions = [
                "execute_sequential",
                "execute_parallel_2",
                "execute_parallel_4",
                "execute_parallel_8",
                "run_all_tests",
                "run_changed_only",
                "run_failed_first"
            ]
        elif self.agent_type == "coverage-analyzer":
            actions = [
                "quick_scan",
                "detailed_analysis",
                "gap_prioritization",
                "use_linear_scan",
                "use_binary_search"
            ]
        else:
            actions = ["default_action"]

        self.q_learning.set_action_space(actions)

    async def execute_with_learning(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task with Q-Learning.

        Args:
            task: Task dictionary with context

        Returns:
            Execution result
        """
        if not self.q_learning:
            # Fall back to regular execution
            return await self.execute_without_learning(task)

        # Define action execution function
        async def execute_action(action: str, context: Dict[str, Any]):
            """Execute the selected action"""
            # This would call the actual agent implementation
            result = await self._execute_action_impl(action, context)

            # Add metadata for learning
            result["action"] = action
            result["done"] = result.get("success", False)  # Episode ends on success
            result["next_context"] = self._extract_next_context(result)

            return result

        # Execute learning episode
        episode_result = await self.q_learning.execute_learning_episode(
            initial_context=task,
            execute_action_fn=execute_action,
            max_steps=10
        )

        return episode_result

    async def _execute_action_impl(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actual action implementation (agent-specific).

        This would be implemented by each agent.
        """
        # Example implementation
        self.logger.info(f"Executing action: {action}")

        # Simulate action execution
        result = {
            "success": True,
            "coverage_percentage": context.get("coverage_percentage", 0) + 5,
            "quality_score": context.get("quality_score", 50) + 2,
            "actual_time_seconds": 30,
            "expected_time_seconds": 45,
            "pattern_reused": False,
            "bugs_found": 1
        }

        return result

    def _extract_next_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract next context from action result"""
        return {
            "coverage_percentage": result.get("coverage_percentage", 0),
            "quality_score": result.get("quality_score", 50),
            "lines_of_code": 1000,
            "task_type": "test_generation"
        }

    async def execute_without_learning(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task without Q-Learning (fallback)"""
        self.logger.info("Executing without Q-Learning")
        # Regular execution logic here
        return {"success": True, "message": "Executed without learning"}


# Example usage
async def example_usage():
    """Example of how to use Q-Learning with an agent"""

    # Create agent with learning enabled
    agent = QEAgentWithLearning(
        agent_id="test-gen-1",
        agent_type="test-generator",
        enable_learning=True
    )

    # Execute task with learning
    task = {
        "task_type": "generate_tests",
        "coverage_percentage": 60.0,
        "quality_score": 70.0,
        "lines_of_code": 500,
        "cyclomatic_complexity": 15,
        "framework": "pytest",
        "test_type": "unit"
    }

    result = await agent.execute_with_learning(task)

    print(f"Episode completed:")
    print(f"  Steps: {result['steps']}")
    print(f"  Total reward: {result['total_reward']:.2f}")
    print(f"  Success rate: {result['success_rate']:.2%}")

    # Get learning statistics
    stats = agent.q_learning.get_statistics()
    print(f"\nLearning statistics:")
    print(f"  Total episodes: {stats['total_episodes']}")
    print(f"  Q-table size: {stats['q_table_size']}")
    print(f"  Epsilon: {stats['epsilon']:.4f}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
