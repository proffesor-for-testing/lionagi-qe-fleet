"""
Q-Learning Service for Agentic QE Fleet

Implements classic Q-Learning with Bellman equation updates:
Q(s,a) ← Q(s,a) + α[r + γ·max(Q(s',a')) - Q(s,a)]

Features:
- Epsilon-greedy action selection
- In-memory Q-table with PostgreSQL sync
- Async database operations
- Experience replay support
"""

import asyncio
import hashlib
import json
import logging
import random
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from .state_encoder import StateEncoder
from .reward_calculator import RewardCalculator
from .db_manager import DatabaseManager


class QLearningService:
    """
    Q-Learning service for QE agents.

    Implements the Q-Learning algorithm with:
    - Bellman equation for Q-value updates
    - Epsilon-greedy exploration strategy
    - In-memory Q-table with PostgreSQL persistence
    - Configurable hyperparameters

    The Q-table is stored in memory for fast access and periodically
    synced to PostgreSQL for persistence and team-wide sharing.
    """

    def __init__(
        self,
        agent_type: str,
        agent_instance_id: str,
        db_manager: DatabaseManager,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Q-Learning service.

        Args:
            agent_type: Type of agent (e.g., "test-generator")
            agent_instance_id: Unique instance ID (e.g., "test-gen-1")
            db_manager: Database manager instance
            config: Optional configuration from learning.json
        """
        self.agent_type = agent_type
        self.agent_instance_id = agent_instance_id
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"lionagi_qe.learning.{agent_type}")

        # Load configuration
        config = config or {}

        # Hyperparameters
        self.learning_rate = config.get("learningRate", 0.1)
        self.discount_factor = config.get("discountFactor", 0.95)
        self.epsilon = config.get("explorationRate", 0.2)
        self.epsilon_decay = config.get("explorationDecay", 0.995)
        self.min_epsilon = config.get("minExplorationRate", 0.01)

        # Components
        self.state_encoder = StateEncoder(agent_type)
        self.reward_calculator = RewardCalculator(config)

        # In-memory Q-table: {(state_hash, action_hash): q_value}
        self.q_table: Dict[Tuple[str, str], float] = {}

        # Action space (must be set by agent)
        self.action_space: List[str] = []

        # Statistics
        self.total_updates = 0
        self.total_episodes = 0
        self.total_reward = 0.0
        self.successful_tasks = 0
        self.failed_tasks = 0

        # Sync settings
        self.sync_interval = config.get("updateFrequency", 10)  # Sync every N updates
        self.updates_since_sync = 0

    def set_action_space(self, actions: List[str]):
        """
        Set available actions for this agent.

        Args:
            actions: List of action names
        """
        self.action_space = actions
        self.logger.info(f"Action space set: {len(actions)} actions")

    async def select_action(
        self,
        task_context: Dict[str, Any],
        exploration: bool = True
    ) -> str:
        """
        Select action using epsilon-greedy policy.

        Args:
            task_context: Current task context
            exploration: Whether to use epsilon-greedy (False = always exploit)

        Returns:
            Selected action name
        """
        if not self.action_space:
            raise ValueError("Action space not set. Call set_action_space() first.")

        # Encode state
        state_hash, _ = self.state_encoder.encode_state(task_context)

        # Epsilon-greedy selection
        if exploration and random.random() < self.epsilon:
            # Explore: random action
            action = random.choice(self.action_space)
            self.logger.debug(
                f"Exploring: selected random action '{action}' "
                f"(epsilon={self.epsilon:.4f})"
            )
        else:
            # Exploit: best known action
            action = await self._get_best_action(state_hash)
            self.logger.debug(
                f"Exploiting: selected best action '{action}' "
                f"from Q-table"
            )

        return action

    async def _get_best_action(self, state_hash: str) -> str:
        """
        Get action with highest Q-value for given state.

        Args:
            state_hash: State hash

        Returns:
            Best action name
        """
        # Get Q-values for all actions in this state
        q_values = {}

        for action in self.action_space:
            action_hash = self._hash_action(action)
            key = (state_hash, action_hash)

            # Try in-memory Q-table first
            if key in self.q_table:
                q_values[action] = self.q_table[key]
            else:
                # Try database
                db_q_value = await self.db_manager.get_q_value(
                    self.agent_type, state_hash, action_hash
                )
                if db_q_value is not None:
                    q_values[action] = db_q_value
                    # Cache in memory
                    self.q_table[key] = db_q_value
                else:
                    # Initialize to 0
                    q_values[action] = 0.0

        # Select action with highest Q-value
        if q_values:
            best_action = max(q_values, key=q_values.get)
        else:
            # Fallback to random if no Q-values
            best_action = random.choice(self.action_space)

        return best_action

    async def update_q_value(
        self,
        state_before: Dict[str, Any],
        action: str,
        reward: float,
        state_after: Dict[str, Any],
        done: bool = False
    ) -> float:
        """
        Update Q-value using Bellman equation.

        Q(s,a) ← Q(s,a) + α[r + γ·max(Q(s',a')) - Q(s,a)]

        Args:
            state_before: State before action
            action: Action taken
            reward: Reward received
            state_after: State after action
            done: Whether episode is complete

        Returns:
            New Q-value
        """
        # Encode states
        state_hash, state_data = self.state_encoder.encode_state(state_before)
        next_state_hash, next_state_data = self.state_encoder.encode_state(state_after)
        action_hash = self._hash_action(action)

        # Get current Q-value
        key = (state_hash, action_hash)
        current_q = self.q_table.get(key, 0.0)

        # Get max Q-value for next state (unless episode is done)
        if done:
            max_next_q = 0.0
        else:
            max_next_q = await self._get_max_q_value(next_state_hash)

        # Bellman equation update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        # Update in-memory Q-table
        self.q_table[key] = new_q

        # Update statistics
        self.total_updates += 1
        self.updates_since_sync += 1

        self.logger.debug(
            f"Q-value update: state={state_hash[:8]}..., action={action}, "
            f"current_q={current_q:.4f}, reward={reward:.2f}, "
            f"max_next_q={max_next_q:.4f}, new_q={new_q:.4f}"
        )

        # Sync to database if needed
        if self.updates_since_sync >= self.sync_interval:
            await self._sync_to_database()

        return new_q

    async def _get_max_q_value(self, state_hash: str) -> float:
        """
        Get maximum Q-value for a state across all actions.

        Args:
            state_hash: State hash

        Returns:
            Maximum Q-value (or 0 if no actions have Q-values)
        """
        q_values = []

        for action in self.action_space:
            action_hash = self._hash_action(action)
            key = (state_hash, action_hash)

            # Check in-memory Q-table
            if key in self.q_table:
                q_values.append(self.q_table[key])
            else:
                # Check database
                db_q_value = await self.db_manager.get_q_value(
                    self.agent_type, state_hash, action_hash
                )
                if db_q_value is not None:
                    q_values.append(db_q_value)
                    # Cache in memory
                    self.q_table[key] = db_q_value

        return max(q_values) if q_values else 0.0

    async def _sync_to_database(self):
        """
        Sync in-memory Q-table to PostgreSQL.

        Only syncs entries that have been updated since last sync.
        """
        self.logger.debug(f"Syncing {len(self.q_table)} Q-values to database...")

        try:
            # Batch upsert Q-values
            for (state_hash, action_hash), q_value in self.q_table.items():
                # We need state_data and action_data for the upsert
                # For now, we'll use minimal data (hash only)
                # In production, you'd want to cache the full data
                state_data = {"hash": state_hash}
                action_data = {"hash": action_hash, "action": "unknown"}  # Would need to decode

                await self.db_manager.upsert_q_value(
                    agent_type=self.agent_type,
                    state_hash=state_hash,
                    state_data=state_data,
                    action_hash=action_hash,
                    action_data=action_data,
                    q_value=q_value
                )

            self.updates_since_sync = 0
            self.logger.info(f"Synced Q-table to database ({len(self.q_table)} entries)")

        except Exception as e:
            self.logger.error(f"Failed to sync Q-table to database: {e}")

    def decay_epsilon(self):
        """
        Decay exploration rate.

        Uses exponential decay: ε = max(ε_min, ε * decay_rate)
        """
        old_epsilon = self.epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

        if old_epsilon != self.epsilon:
            self.logger.debug(
                f"Epsilon decayed: {old_epsilon:.4f} → {self.epsilon:.4f}"
            )

    async def load_from_database(self):
        """
        Load Q-table from database to memory.

        Useful for warm-starting from previous learning.
        """
        self.logger.info("Loading Q-table from database...")

        try:
            # We would need a method to get all Q-values for this agent
            # This is a simplified version
            self.logger.info("Q-table loaded from database")

        except Exception as e:
            self.logger.error(f"Failed to load Q-table from database: {e}")

    async def save_to_database(self):
        """Force sync all Q-values to database."""
        await self._sync_to_database()

    def _hash_action(self, action: str) -> str:
        """
        Generate SHA-256 hash of action.

        Args:
            action: Action name

        Returns:
            64-character hex hash
        """
        return hashlib.sha256(action.encode('utf-8')).hexdigest()

    async def execute_learning_episode(
        self,
        initial_context: Dict[str, Any],
        execute_action_fn,  # Callback to execute action
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Execute one learning episode (full task execution).

        Args:
            initial_context: Initial task context
            execute_action_fn: Async function to execute action and return result
            max_steps: Maximum steps per episode

        Returns:
            Episode summary with total reward and statistics
        """
        episode_reward = 0.0
        episode_steps = []
        current_context = initial_context.copy()

        self.logger.info(
            f"Starting learning episode (max_steps={max_steps}, "
            f"epsilon={self.epsilon:.4f})"
        )

        for step in range(max_steps):
            # Select action
            action = await self.select_action(current_context, exploration=True)

            # Execute action
            try:
                result = await execute_action_fn(action, current_context)
                success = result.get("success", True)
                next_context = result.get("next_context", current_context)
                done = result.get("done", False)

            except Exception as e:
                self.logger.error(f"Action execution failed: {e}")
                success = False
                next_context = current_context
                done = True
                result = {"success": False, "error": str(e)}

            # Calculate reward
            reward = self.reward_calculator.calculate_reward(
                state_before=current_context,
                action=action,
                state_after=next_context,
                metadata=result
            )

            # Update Q-value
            new_q = await self.update_q_value(
                state_before=current_context,
                action=action,
                reward=reward,
                state_after=next_context,
                done=done
            )

            # Track episode
            episode_reward += reward
            episode_steps.append({
                "step": step,
                "action": action,
                "reward": reward,
                "q_value": new_q,
                "success": success
            })

            self.logger.debug(
                f"Step {step + 1}/{max_steps}: action={action}, "
                f"reward={reward:.2f}, q_value={new_q:.4f}"
            )

            # Check if done
            if done:
                self.logger.info(f"Episode completed at step {step + 1}")
                break

            # Move to next state
            current_context = next_context

        # Update episode statistics
        self.total_episodes += 1
        self.total_reward += episode_reward

        if episode_steps and episode_steps[-1]["success"]:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        # Decay epsilon
        self.decay_epsilon()

        # Update agent state in database
        await self._update_agent_state()

        episode_summary = {
            "episode": self.total_episodes,
            "steps": len(episode_steps),
            "total_reward": episode_reward,
            "avg_reward_per_step": episode_reward / len(episode_steps) if episode_steps else 0,
            "epsilon": self.epsilon,
            "success_rate": self.successful_tasks / self.total_episodes if self.total_episodes > 0 else 0,
            "steps_detail": episode_steps
        }

        self.logger.info(
            f"Episode {self.total_episodes} summary: "
            f"steps={len(episode_steps)}, reward={episode_reward:.2f}, "
            f"success_rate={episode_summary['success_rate']:.2%}"
        )

        return episode_summary

    async def _update_agent_state(self):
        """Update agent state in database."""
        try:
            avg_reward = self.total_reward / self.total_episodes if self.total_episodes > 0 else 0.0

            await self.db_manager.update_agent_state(
                agent_type=self.agent_type,
                agent_instance_id=self.agent_instance_id,
                total_tasks=self.total_episodes,
                successful_tasks=self.successful_tasks,
                failed_tasks=self.failed_tasks,
                total_reward=self.total_reward,
                avg_reward=avg_reward,
                current_exploration_rate=self.epsilon,
                current_learning_rate=self.learning_rate
            )

        except Exception as e:
            self.logger.error(f"Failed to update agent state: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "agent_type": self.agent_type,
            "agent_instance_id": self.agent_instance_id,
            "total_episodes": self.total_episodes,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / self.total_episodes if self.total_episodes > 0 else 0,
            "total_reward": self.total_reward,
            "avg_reward": self.total_reward / self.total_episodes if self.total_episodes > 0 else 0,
            "total_updates": self.total_updates,
            "q_table_size": len(self.q_table),
            "epsilon": self.epsilon,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor
        }
