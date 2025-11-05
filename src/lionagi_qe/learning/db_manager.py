"""
Database Manager for Q-Learning

Handles PostgreSQL operations for Q-values, trajectories, and learning statistics.
Uses asyncpg for async database operations with connection pooling.
"""

import asyncpg
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta


class DatabaseManager:
    """
    Manages PostgreSQL database operations for Q-learning.

    Provides async CRUD operations for:
    - Q-values (state-action-value tuples)
    - Trajectories (execution episodes)
    - Learning statistics
    - Agent states

    Uses connection pooling for efficiency.
    """

    def __init__(
        self,
        database_url: str,
        min_connections: int = 2,
        max_connections: int = 10
    ):
        """
        Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger("lionagi_qe.learning.db")

    async def connect(self):
        """Create connection pool."""
        if self.pool is None:
            self.logger.info("Creating database connection pool...")
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=60
            )
            self.logger.info("Database connection pool created")

    async def disconnect(self):
        """Close connection pool."""
        if self.pool is not None:
            self.logger.info("Closing database connection pool...")
            await self.pool.close()
            self.pool = None
            self.logger.info("Database connection pool closed")

    async def get_q_value(
        self,
        agent_type: str,
        state_hash: str,
        action_hash: str
    ) -> Optional[float]:
        """
        Get Q-value for state-action pair.

        Args:
            agent_type: Type of agent
            state_hash: SHA-256 hash of state
            action_hash: SHA-256 hash of action

        Returns:
            Q-value or None if not found
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT q_value
                FROM q_values
                WHERE agent_type = $1 AND state_hash = $2 AND action_hash = $3
                """,
                agent_type, state_hash, action_hash
            )

            return row['q_value'] if row else None

    async def upsert_q_value(
        self,
        agent_type: str,
        state_hash: str,
        state_data: Dict[str, Any],
        action_hash: str,
        action_data: Dict[str, Any],
        q_value: float,
        session_id: Optional[str] = None
    ) -> int:
        """
        Insert or update Q-value using database function.

        Args:
            agent_type: Type of agent
            state_hash: SHA-256 hash of state
            state_data: Full state representation
            action_hash: SHA-256 hash of action
            action_data: Full action representation
            q_value: New Q-value
            session_id: Optional session ID

        Returns:
            Q-value ID
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            # Use the database function for atomic upsert
            q_value_id = await conn.fetchval(
                """
                SELECT upsert_q_value($1, $2, $3, $4, $5, $6, $7)
                """,
                agent_type,
                state_hash,
                json.dumps(state_data),
                action_hash,
                json.dumps(action_data),
                q_value,
                session_id
            )

            self.logger.debug(
                f"Upserted Q-value for {agent_type}: "
                f"state={state_hash[:8]}..., action={action_hash[:8]}..., "
                f"q_value={q_value:.4f}"
            )

            return q_value_id

    async def get_best_action(
        self,
        agent_type: str,
        state_hash: str
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Get best action for given state.

        Args:
            agent_type: Type of agent
            state_hash: SHA-256 hash of state

        Returns:
            Tuple of (action_data, q_value) or None if no actions found
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT action_data, q_value
                FROM get_best_action($1, $2)
                """,
                agent_type, state_hash
            )

            if row:
                return (json.loads(row['action_data']), row['q_value'])
            else:
                return None

    async def get_all_q_values_for_state(
        self,
        agent_type: str,
        state_hash: str
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Get all Q-values for a given state.

        Args:
            agent_type: Type of agent
            state_hash: SHA-256 hash of state

        Returns:
            List of (action_data, q_value) tuples
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT action_data, q_value
                FROM q_values
                WHERE agent_type = $1 AND state_hash = $2
                ORDER BY q_value DESC
                """,
                agent_type, state_hash
            )

            return [
                (json.loads(row['action_data']), row['q_value'])
                for row in rows
            ]

    async def store_trajectory(
        self,
        agent_type: str,
        session_id: str,
        task_id: str,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
        actions_taken: List[Dict[str, Any]],
        states_visited: List[Dict[str, Any]],
        step_rewards: List[float],
        total_reward: float,
        discounted_reward: float,
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store execution trajectory.

        Args:
            agent_type: Type of agent
            session_id: Session ID
            task_id: Task ID
            initial_state: Starting state
            final_state: Ending state
            actions_taken: List of actions
            states_visited: List of states
            step_rewards: Reward at each step
            total_reward: Sum of rewards
            discounted_reward: Discounted reward
            execution_time_ms: Execution time in milliseconds
            success: Whether task succeeded
            error_message: Optional error message
            metadata: Optional metadata

        Returns:
            Trajectory ID
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            trajectory_id = await conn.fetchval(
                """
                INSERT INTO trajectories (
                    agent_type, session_id, task_id,
                    initial_state, final_state,
                    actions_taken, states_visited,
                    step_rewards, total_reward, discounted_reward,
                    execution_time_ms, success, error_message,
                    started_at, completed_at,
                    expires_at, metadata
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, NOW() - INTERVAL '1 second' * ($11::float / 1000),
                    NOW(), NOW() + INTERVAL '30 days', $14
                )
                RETURNING trajectory_id
                """,
                agent_type, session_id, task_id,
                json.dumps(initial_state), json.dumps(final_state),
                json.dumps(actions_taken), json.dumps(states_visited),
                json.dumps(step_rewards), total_reward, discounted_reward,
                execution_time_ms, success, error_message,
                json.dumps(metadata or {})
            )

            self.logger.debug(
                f"Stored trajectory {trajectory_id} for {agent_type}: "
                f"success={success}, reward={total_reward:.2f}"
            )

            return str(trajectory_id)

    async def get_recent_trajectories(
        self,
        agent_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent trajectories for an agent.

        Args:
            agent_type: Type of agent
            limit: Maximum number of trajectories

        Returns:
            List of trajectory dictionaries
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    trajectory_id, task_id,
                    initial_state, final_state,
                    actions_taken, states_visited,
                    step_rewards, total_reward,
                    execution_time_ms, success,
                    completed_at, metadata
                FROM trajectories
                WHERE agent_type = $1
                ORDER BY completed_at DESC
                LIMIT $2
                """,
                agent_type, limit
            )

            return [
                {
                    "trajectory_id": str(row['trajectory_id']),
                    "task_id": row['task_id'],
                    "initial_state": json.loads(row['initial_state']),
                    "final_state": json.loads(row['final_state']),
                    "actions_taken": json.loads(row['actions_taken']),
                    "states_visited": json.loads(row['states_visited']),
                    "step_rewards": json.loads(row['step_rewards']),
                    "total_reward": float(row['total_reward']),
                    "execution_time_ms": row['execution_time_ms'],
                    "success": row['success'],
                    "completed_at": row['completed_at'].isoformat(),
                    "metadata": json.loads(row['metadata'])
                }
                for row in rows
            ]

    async def update_agent_state(
        self,
        agent_type: str,
        agent_instance_id: str,
        total_tasks: int,
        successful_tasks: int,
        failed_tasks: int,
        total_reward: float,
        avg_reward: float,
        current_exploration_rate: float,
        current_learning_rate: float
    ):
        """
        Update agent state statistics.

        Args:
            agent_type: Type of agent
            agent_instance_id: Instance ID
            total_tasks: Total tasks completed
            successful_tasks: Successful tasks
            failed_tasks: Failed tasks
            total_reward: Total reward accumulated
            avg_reward: Average reward
            current_exploration_rate: Current epsilon
            current_learning_rate: Current alpha
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_states (
                    agent_type, agent_instance_id,
                    total_tasks, successful_tasks, failed_tasks,
                    total_reward, avg_reward,
                    current_exploration_rate, current_learning_rate,
                    status, last_activity
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active', NOW())
                ON CONFLICT (agent_type, agent_instance_id)
                DO UPDATE SET
                    total_tasks = $3,
                    successful_tasks = $4,
                    failed_tasks = $5,
                    total_reward = $6,
                    avg_reward = $7,
                    current_exploration_rate = $8,
                    current_learning_rate = $9,
                    last_activity = NOW(),
                    updated_at = NOW()
                """,
                agent_type, agent_instance_id,
                total_tasks, successful_tasks, failed_tasks,
                total_reward, avg_reward,
                current_exploration_rate, current_learning_rate
            )

            self.logger.debug(
                f"Updated agent state for {agent_type}/{agent_instance_id}: "
                f"tasks={total_tasks}, avg_reward={avg_reward:.2f}"
            )

    async def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired records.

        Returns:
            Dictionary with counts of deleted records per table
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM cleanup_expired_data()")

            result = {}
            for row in rows:
                result[row['table_name']] = row['deleted_count']

            self.logger.info(f"Cleaned up expired data: {result}")

            return result

    async def get_learning_statistics(
        self,
        agent_type: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get learning statistics for an agent.

        Args:
            agent_type: Type of agent
            hours: Number of hours to look back

        Returns:
            List of statistics dictionaries
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as conn:
            # First get the q_table_id
            q_table_id = await conn.fetchval(
                "SELECT id FROM q_tables WHERE agent_id = $1 AND scope = 'individual'",
                agent_type
            )

            if not q_table_id:
                return []

            rows = await conn.fetch(
                """
                SELECT
                    window_start, window_end,
                    episodes_completed, avg_episode_reward, std_episode_reward,
                    avg_q_value_change, exploration_rate,
                    avg_task_duration_seconds, success_rate
                FROM learning_stats
                WHERE q_table_id = $1
                  AND window_start >= NOW() - INTERVAL '1 hour' * $2
                ORDER BY window_start DESC
                """,
                q_table_id, hours
            )

            return [
                {
                    "window_start": row['window_start'].isoformat(),
                    "window_end": row['window_end'].isoformat(),
                    "episodes_completed": row['episodes_completed'],
                    "avg_episode_reward": float(row['avg_episode_reward']) if row['avg_episode_reward'] else 0.0,
                    "std_episode_reward": float(row['std_episode_reward']) if row['std_episode_reward'] else 0.0,
                    "avg_q_value_change": float(row['avg_q_value_change']) if row['avg_q_value_change'] else 0.0,
                    "exploration_rate": float(row['exploration_rate']) if row['exploration_rate'] else 0.0,
                    "avg_task_duration_seconds": float(row['avg_task_duration_seconds']) if row['avg_task_duration_seconds'] else 0.0,
                    "success_rate": float(row['success_rate']) if row['success_rate'] else 0.0
                }
                for row in rows
            ]
