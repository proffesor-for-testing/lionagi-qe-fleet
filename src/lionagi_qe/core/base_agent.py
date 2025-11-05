"""Base class for all QE agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, Union, Tuple
from lionagi import Branch, iModel
from .task import QETask
from .memory import QEMemory
import logging
import hashlib
import json
import warnings

# Generic type for Pydantic models
try:
    from pydantic import BaseModel
    T = TypeVar('T', bound=BaseModel)
except ImportError:
    # Fallback if pydantic not available
    BaseModel = object
    T = TypeVar('T')

# Import fuzzy parsing utilities from LionAGI
try:
    from lionagi.ln.fuzzy import fuzzy_json, fuzzy_validate_pydantic
    FUZZY_PARSING_AVAILABLE = True
except ImportError:
    # Graceful fallback if fuzzy parsing not available
    FUZZY_PARSING_AVAILABLE = False
    fuzzy_json = None
    fuzzy_validate_pydantic = None

# Import Q-Learning components (optional, graceful fallback)
try:
    from lionagi_qe.learning import QLearningService, StateEncoder, RewardCalculator
    QLEARNING_AVAILABLE = True
except ImportError:
    # Q-Learning not yet implemented - graceful fallback
    QLEARNING_AVAILABLE = False
    QLearningService = None
    StateEncoder = None
    RewardCalculator = None


class BaseQEAgent(ABC):
    """Base class for all QE agents

    All specialized QE agents inherit from this base class and implement:
    - get_system_prompt(): Define agent expertise
    - execute(): Main agent logic

    Agents automatically integrate with:
    - LionAGI Branch for conversations
    - Persistent memory backends (PostgreSQL, Redis, or in-memory)
    - Multi-model routing
    - Skill registry
    - Q-learning (optional)

    Memory Backend Options:
        1. PostgresMemory (recommended for production):
           - Reuses Q-learning database infrastructure
           - ACID guarantees
           - Full persistence
           - Example:
             ```python
             from lionagi_qe.learning import DatabaseManager
             from lionagi_qe.persistence import PostgresMemory

             db_manager = DatabaseManager("postgresql://...")
             await db_manager.connect()
             memory = PostgresMemory(db_manager)
             agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)
             ```

        2. RedisMemory (high-speed cache):
           - Sub-millisecond latency
           - Native TTL support
           - Optional persistence
           - Example:
             ```python
             from lionagi_qe.persistence import RedisMemory

             memory = RedisMemory(host="localhost")
             agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)
             ```

        3. Session.context (default, in-memory):
           - Zero setup
           - Development use
           - No persistence
           - Example:
             ```python
             agent = BaseQEAgent(agent_id="test-gen", model=model)
             ```

        4. QEMemory (deprecated):
           - In-memory only
           - No persistence
           - Will show deprecation warning
    """

    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: Optional[Any] = None,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional['QLearningService'] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize QE agent

        Args:
            agent_id: Unique agent identifier (e.g., "test-generator")
            model: LionAGI model instance
            memory: Memory backend (None = auto-detect, QEMemory = deprecated,
                   PostgresMemory/RedisMemory = persistent)
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
            q_learning_service: Optional Q-learning service instance
            memory_config: Optional config for auto-initializing memory backend
                         Example: {"type": "postgres", "db_manager": db_mgr}
                                 {"type": "redis", "host": "localhost"}
                                 {"type": "session"}  # Use Session.context

        Examples:
            # Option 1: Pass memory backend directly
            memory = PostgresMemory(db_manager)
            agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)

            # Option 2: Auto-initialize from config
            agent = BaseQEAgent(
                agent_id="test-gen",
                model=model,
                memory_config={"type": "postgres", "db_manager": db_manager}
            )

            # Option 3: Default (Session.context)
            agent = BaseQEAgent(agent_id="test-gen", model=model)

        Migration from QEMemory:
            # Before (deprecated)
            from lionagi_qe.core.memory import QEMemory
            memory = QEMemory()
            agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)

            # After - Option 1: PostgreSQL (recommended for production)
            from lionagi_qe.learning import DatabaseManager
            from lionagi_qe.persistence import PostgresMemory

            db_manager = DatabaseManager("postgresql://...")
            await db_manager.connect()
            memory = PostgresMemory(db_manager)
            agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)

            # After - Option 2: Redis (high-speed cache)
            from lionagi_qe.persistence import RedisMemory
            memory = RedisMemory(host="localhost")
            agent = BaseQEAgent(agent_id="test-gen", model=model, memory=memory)

            # After - Option 3: In-memory (development)
            agent = BaseQEAgent(agent_id="test-gen", model=model)  # Uses Session.context
        """
        self.agent_id = agent_id
        self.model = model

        # Memory initialization with backward compatibility
        self.memory = self._initialize_memory(memory, memory_config)

        self.skills = skills or []
        self.enable_learning = enable_learning

        # Q-Learning integration
        self.q_service = q_learning_service if QLEARNING_AVAILABLE else None
        self.current_state_hash: Optional[str] = None
        self.current_action_id: Optional[str] = None

        # Initialize LionAGI branch for conversations
        self.branch = Branch(
            system=self.get_system_prompt(),
            chat_model=model,
            name=agent_id
        )

        # Setup logging
        self.logger = logging.getLogger(f"lionagi_qe.{agent_id}")

        # Execution metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_cost": 0.0,
            "patterns_learned": 0,
            "total_reward": 0.0,
            "avg_reward": 0.0,
            "learning_episodes": 0,
        }

    def _initialize_memory(
        self,
        memory: Optional[Any],
        memory_config: Optional[Dict[str, Any]]
    ) -> Any:
        """Initialize memory backend with backward compatibility

        Supports:
        - None: Auto-detect (Session.context or from config)
        - QEMemory: Deprecated (warn user)
        - PostgresMemory/RedisMemory: Persistent backends
        - Dict-like: Custom backend

        Args:
            memory: Memory instance or None
            memory_config: Configuration for auto-initialization

        Returns:
            Memory backend instance
        """
        # Case 1: Memory instance provided
        if memory is not None:
            if isinstance(memory, QEMemory):
                warnings.warn(
                    f"QEMemory is deprecated and lacks persistence. "
                    f"Consider using PostgresMemory or RedisMemory for production. "
                    f"Agent: {self.agent_id}",
                    DeprecationWarning,
                    stacklevel=3
                )
            return memory

        # Case 2: Auto-initialize from config
        if memory_config:
            backend_type = memory_config.get("type", "session")

            if backend_type == "postgres":
                try:
                    from lionagi_qe.persistence import PostgresMemory
                except ImportError:
                    raise ImportError(
                        "PostgresMemory requires 'lionagi-qe-fleet' package. "
                        "Install with: pip install lionagi-qe-fleet"
                    )
                db_manager = memory_config.get("db_manager")
                if not db_manager:
                    raise ValueError("PostgresMemory requires 'db_manager' in memory_config")
                return PostgresMemory(db_manager)

            elif backend_type == "redis":
                try:
                    from lionagi_qe.persistence import RedisMemory
                except ImportError:
                    raise ImportError(
                        "RedisMemory requires redis package. "
                        "Install with: pip install lionagi-qe-fleet[persistence]"
                    )
                return RedisMemory(
                    host=memory_config.get("host", "localhost"),
                    port=memory_config.get("port", 6379),
                    db=memory_config.get("db", 0),
                    password=memory_config.get("password")
                )

            elif backend_type == "session":
                from lionagi import Session
                if not hasattr(self, '_session'):
                    self._session = Session()
                return self._session.context

            else:
                raise ValueError(f"Unknown memory backend type: {backend_type}")

        # Case 3: Default to Session.context
        from lionagi import Session
        if not hasattr(self, '_session'):
            self._session = Session()
        return self._session.context

    @property
    def memory_backend_type(self) -> str:
        """Get type of memory backend in use

        Returns:
            "postgres", "redis", "qememory", "session", or "custom"
        """
        if hasattr(self.memory, '__class__'):
            class_name = self.memory.__class__.__name__
            if class_name == "PostgresMemory":
                return "postgres"
            elif class_name == "RedisMemory":
                return "redis"
            elif class_name == "QEMemory":
                return "qememory"
            elif "Session" in str(type(self.memory)) or "Context" in class_name:
                return "session"
        return "custom"

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Define agent's expertise and behavior

        Returns:
            System prompt describing agent capabilities
        """
        pass

    @abstractmethod
    async def execute(self, task: QETask) -> Dict[str, Any]:
        """Execute agent's primary function

        Args:
            task: QE task to execute

        Returns:
            Task execution result
        """
        pass

    async def store_result(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        partition: str = "agent_results"
    ):
        """Store results in shared memory

        Args:
            key: Memory key (will be prefixed with aqe/{agent_id}/)
            value: Value to store
            ttl: Time-to-live in seconds
            partition: Memory partition
        """
        full_key = f"aqe/{self.agent_id}/{key}"
        await self.memory.store(full_key, value, ttl=ttl, partition=partition)
        self.logger.debug(f"Stored result: {full_key}")

    async def retrieve_context(self, key: str) -> Any:
        """Retrieve context from shared memory

        Args:
            key: Memory key to retrieve

        Returns:
            Stored value or None
        """
        value = await self.memory.retrieve(key)
        self.logger.debug(f"Retrieved context: {key} = {value is not None}")
        return value

    async def get_memory(self, key: str, default: Any = None) -> Any:
        """Retrieve value from shared memory with default fallback

        This is a convenience method for agents to retrieve values from
        the shared memory namespace with a default value if the key doesn't exist.

        Args:
            key: Memory key to retrieve (e.g., "aqe/quality/config")
            default: Default value to return if key not found

        Returns:
            Stored value or default
        """
        value = await self.memory.retrieve(key)
        if value is None:
            value = default
        self.logger.debug(f"Retrieved memory: {key} = {value is not None}")
        return value

    async def store_memory(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        partition: str = "agent_data"
    ):
        """Store value in shared memory

        This is a convenience method for agents to store values in
        the shared memory namespace without the aqe/{agent_id}/ prefix.

        Args:
            key: Memory key (e.g., "aqe/coverage/gaps")
            value: Value to store
            ttl: Time-to-live in seconds
            partition: Memory partition
        """
        await self.memory.store(key, value, ttl=ttl, partition=partition)
        self.logger.debug(f"Stored memory: {key}")

    async def search_memory(self, pattern: str) -> Dict[str, Any]:
        """Search memory using regex pattern

        Args:
            pattern: Regex pattern to match keys

        Returns:
            Dict of matching keys and values
        """
        return await self.memory.search(pattern)

    async def get_learned_patterns(self) -> Dict[str, Any]:
        """Retrieve learned patterns from memory

        Returns:
            Dict of learned patterns for this agent type
        """
        patterns = await self.search_memory(
            f"aqe/patterns/{self.agent_id}/.*"
        )
        return patterns

    async def store_learned_pattern(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any]
    ):
        """Store learned pattern for future use

        Args:
            pattern_name: Name of the pattern
            pattern_data: Pattern data to store
        """
        key = f"aqe/patterns/{self.agent_id}/{pattern_name}"
        await self.memory.store(key, pattern_data, partition="patterns")
        self.metrics["patterns_learned"] += 1

    async def pre_execution_hook(self, task: QETask):
        """Hook called before task execution

        Override to implement pre-execution logic like:
        - Loading context from memory
        - Validating task parameters
        - Setting up resources
        """
        self.logger.info(f"Starting task: {task.task_type} ({task.task_id})")

    async def post_execution_hook(
        self,
        task: QETask,
        result: Dict[str, Any]
    ):
        """Hook called after successful task execution

        Override to implement post-execution logic like:
        - Storing results
        - Updating metrics
        - Learning from execution
        """
        self.logger.info(f"Completed task: {task.task_type} ({task.task_id})")
        self.metrics["tasks_completed"] += 1

        # Store result in memory
        await self.store_result(
            f"tasks/{task.task_id}/result",
            result,
            ttl=86400  # 24 hours
        )

        # Learn from execution if enabled
        if self.enable_learning:
            await self._learn_from_execution(task, result)

    async def error_handler(self, task: QETask, error: Exception):
        """Handle execution errors

        Args:
            task: Task that failed
            error: Exception that occurred
        """
        self.logger.error(
            f"Task failed: {task.task_type} ({task.task_id}) - {str(error)}"
        )
        self.metrics["tasks_failed"] += 1

        # Store error in memory
        await self.store_result(
            f"tasks/{task.task_id}/error",
            {
                "error": str(error),
                "task_type": task.task_type,
                "context": task.context,
            },
            ttl=604800  # 7 days
        )

    async def _learn_from_execution(
        self,
        task: QETask,
        result: Dict[str, Any]
    ):
        """Learn from task execution using Q-learning

        This method implements the full Q-learning update cycle:
        1. Encode current state from task context
        2. Calculate reward based on task result
        3. Encode next state (terminal or from result)
        4. Update Q-value using Bellman equation: Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        5. Store trajectory (SARS') in database for experience replay
        6. Decay epsilon for exploration-exploitation balance

        Flow:
            Task execution → State encoding → Reward calculation →
            Next state encoding → Q-value update → Trajectory storage → Epsilon decay

        Args:
            task: Completed task with context
            result: Execution result containing outcome metrics
        """
        if not self.enable_learning:
            self.logger.debug("Learning disabled, skipping Q-learning update")
            return

        if not QLEARNING_AVAILABLE:
            # Q-Learning module not yet available - store trajectories only
            self.logger.debug("Q-Learning module not available, storing trajectory for future use")
            trajectory = {
                "task_type": task.task_type,
                "context": task.context,
                "result": result,
                "success": result.get("success", True),
                "timestamp": result.get("timestamp", None),
            }
            await self.store_result(
                f"learning/trajectories/{task.task_id}",
                trajectory,
                ttl=2592000,  # 30 days
                partition="learning"
            )
            return

        if not self.q_service:
            self.logger.warning("Q-learning enabled but service not initialized")
            return

        try:
            self.logger.debug(f"Starting Q-learning update for task {task.task_id}")

            # 1. Encode current state from task context
            state_data = self._extract_state_from_task(task)
            state_hash = self._hash_state(state_data)
            self.logger.debug(f"Encoded state: {state_hash[:16]}... with {len(state_data)} features")

            # 2. Get action that was taken (from current_action_id or infer from result)
            action_id = self.current_action_id or self._infer_action_from_result(result)
            if not action_id:
                self.logger.warning("Cannot determine action taken, skipping Q-learning update")
                return

            # 3. Calculate reward from result
            reward = self._calculate_reward(task, result, state_data)
            self.logger.info(f"Calculated reward: {reward:.2f} for action {action_id}")

            # Update metrics
            self.metrics["total_reward"] += reward
            self.metrics["learning_episodes"] += 1
            self.metrics["avg_reward"] = (
                self.metrics["total_reward"] / self.metrics["learning_episodes"]
            )

            # 4. Encode next state (terminal if task complete, otherwise from result)
            is_terminal = result.get("done", True)
            if is_terminal:
                next_state_hash = None  # Terminal state
                self.logger.debug("Terminal state reached")
            else:
                next_state_data = self._extract_state_from_result(result)
                next_state_hash = self._hash_state(next_state_data)
                self.logger.debug(f"Encoded next state: {next_state_hash[:16]}...")

            # 5. Update Q-value using Bellman equation
            # Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
            await self.q_service.update_q_value(
                agent_id=self.agent_id,
                state_hash=state_hash,
                action_id=action_id,
                reward=reward,
                next_state_hash=next_state_hash,
                is_terminal=is_terminal
            )
            self.logger.debug("Q-value updated successfully")

            # 6. Store full trajectory (SARS') for experience replay
            await self._store_trajectory(
                state_hash=state_hash,
                state_data=state_data,
                action_id=action_id,
                reward=reward,
                next_state_hash=next_state_hash,
                next_state_data=next_state_data if not is_terminal else None,
                task_id=task.task_id,
                metadata=result
            )
            self.logger.debug("Trajectory stored for experience replay")

            # 7. Decay epsilon (reduce exploration over time)
            await self._decay_epsilon(reward)

            self.logger.info(
                f"Q-learning update complete: reward={reward:.2f}, "
                f"avg_reward={self.metrics['avg_reward']:.2f}, "
                f"episodes={self.metrics['learning_episodes']}"
            )

        except Exception as e:
            self.logger.error(f"Q-learning update failed: {e}", exc_info=True)
            # Don't fail the task if learning fails - graceful degradation

    async def execute_with_learning(self, task: QETask) -> Dict[str, Any]:
        """Execute task with Q-learning action selection

        This method integrates Q-learning into the task execution cycle:
        1. Encode state from task
        2. Select action using epsilon-greedy policy (explore vs exploit)
        3. Execute the selected action
        4. Calculate reward based on outcome
        5. Update Q-value (done in post_execution_hook → _learn_from_execution)
        6. Return result with learning metrics

        The learning loop:
            State → Action Selection → Execute → Reward → Update Q-value → Next State

        Args:
            task: QE task to execute with learning

        Returns:
            Dict containing:
            - Task execution result
            - Learning metrics (reward, action, state_hash, exploration_used)
            - Performance data

        Example:
            ```python
            result = await agent.execute_with_learning(task)
            print(f"Reward: {result['learning']['reward']}")
            print(f"Action: {result['learning']['action_selected']}")
            ```
        """
        if not self.enable_learning or not QLEARNING_AVAILABLE or not self.q_service:
            # Fall back to standard execution if learning not available
            self.logger.debug("Learning not available, falling back to standard execution")
            return await self.execute(task)

        try:
            self.logger.info(f"Executing task with Q-learning: {task.task_id}")

            # 1. Encode current state from task
            state_data = self._extract_state_from_task(task)
            state_hash = self._hash_state(state_data)
            self.current_state_hash = state_hash
            self.logger.debug(f"State encoded: {state_hash[:16]}...")

            # 2. Select action using epsilon-greedy policy
            action_id, exploration_used = await self.q_service.select_action(
                agent_id=self.agent_id,
                state_hash=state_hash,
                available_actions=self._get_available_actions(task)
            )
            self.current_action_id = action_id
            self.logger.info(
                f"Selected action: {action_id} "
                f"({'exploration' if exploration_used else 'exploitation'})"
            )

            # 3. Execute the action
            # Subclasses implement execute() to perform the actual task
            # The action_id influences behavior (stored in current_action_id)
            execution_start = self._get_timestamp()
            result = await self.execute(task)
            execution_time = self._get_timestamp() - execution_start

            # 4. Enhance result with learning metrics
            result["learning"] = {
                "action_selected": action_id,
                "state_hash": state_hash,
                "exploration_used": exploration_used,
                "execution_time_seconds": execution_time,
            }

            # Note: Reward calculation and Q-value update happen in
            # post_execution_hook → _learn_from_execution

            self.logger.info(
                f"Task executed with learning: {task.task_id}, "
                f"action={action_id}, time={execution_time:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Q-learning execution failed: {e}", exc_info=True)
            # Fall back to standard execution on error
            self.logger.warning("Falling back to standard execution due to error")
            return await self.execute(task)

    # ============================================================================
    # Helper Methods for Q-Learning Integration
    # ============================================================================

    def _extract_state_from_task(self, task: QETask) -> Dict[str, Any]:
        """Extract state features from task for Q-learning

        This is a default implementation that extracts basic features.
        Subclasses should override to add agent-specific state features.

        Args:
            task: QE task to extract state from

        Returns:
            Dict of state features (will be hashed for Q-table lookup)

        Example override in TestGeneratorAgent:
            ```python
            def _extract_state_from_task(self, task: QETask) -> Dict[str, Any]:
                state = super()._extract_state_from_task(task)
                state.update({
                    "code_complexity": self._analyze_complexity(task.context),
                    "coverage_gap": self._get_coverage_gap(task.context),
                    "framework": task.context.get("framework", "pytest")
                })
                return state
            ```
        """
        return {
            "task_type": task.task_type,
            "agent_id": self.agent_id,
            # Add basic context features
            "has_context": bool(task.context),
            "context_size": len(str(task.context)) if task.context else 0,
        }

    def _extract_state_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract next state features from execution result

        Args:
            result: Execution result containing outcome

        Returns:
            Dict of next state features
        """
        return {
            "success": result.get("success", False),
            "result_type": result.get("type", "unknown"),
            "has_data": bool(result.get("data")),
        }

    def _hash_state(self, state_data: Dict[str, Any]) -> str:
        """Hash state dictionary to create state identifier

        Uses SHA-256 for consistent, deterministic hashing.

        Args:
            state_data: State features dictionary

        Returns:
            64-character hex hash string
        """
        # Sort keys for deterministic hashing
        state_str = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()

    def _get_available_actions(self, task: QETask) -> List[str]:
        """Get list of available actions for current task

        This is a default implementation that returns generic actions.
        Subclasses should override to provide agent-specific actions.

        Args:
            task: Current task

        Returns:
            List of action IDs

        Example override:
            ```python
            def _get_available_actions(self, task: QETask) -> List[str]:
                if task.task_type == "generate_tests":
                    return ["property_based", "example_based", "mutation"]
                return ["default_action"]
            ```
        """
        return ["default_action", "alternative_action"]

    def _infer_action_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """Infer action that was taken from execution result

        Used when current_action_id is not set (backward compatibility).

        Args:
            result: Execution result

        Returns:
            Action ID or None if cannot infer
        """
        # Check if result contains action information
        if "learning" in result and "action_selected" in result["learning"]:
            return result["learning"]["action_selected"]

        # Default action if cannot infer
        return "default_action"

    def _calculate_reward(
        self,
        task: QETask,
        result: Dict[str, Any],
        state_data: Dict[str, Any]
    ) -> float:
        """Calculate reward for Q-learning update

        This is a default multi-objective reward function.
        Subclasses should override to provide agent-specific rewards.

        Default reward components:
        1. Success/failure: +50 / -50 points
        2. Execution speed: Based on actual vs expected time
        3. Quality improvement: Based on metrics

        Args:
            task: Completed task
            result: Execution result
            state_data: State features

        Returns:
            Reward value (typically -100 to +100)

        Example override:
            ```python
            def _calculate_reward(self, task, result, state_data) -> float:
                base_reward = super()._calculate_reward(task, result, state_data)

                # Add test-specific rewards
                coverage_gain = result.get("coverage_gain", 0)
                tests_generated = result.get("tests_count", 0)

                coverage_reward = coverage_gain * 10  # 1% = 10 points
                efficiency_penalty = abs(tests_generated - 10) * -2

                return base_reward + coverage_reward + efficiency_penalty
            ```
        """
        reward = 0.0

        # 1. Success/failure reward
        if result.get("success", False):
            reward += 50.0
        else:
            reward -= 50.0

        # 2. Execution speed reward
        expected_time = task.context.get("expected_time_seconds", 60)
        actual_time = result.get("execution_time_seconds", expected_time)
        if actual_time > 0:
            time_ratio = expected_time / actual_time
            # Faster than expected: positive, slower: negative
            reward += (time_ratio - 1.0) * 20.0

        # 3. Quality improvement reward
        quality_delta = result.get("quality_improvement", 0.0)
        reward += quality_delta * 2.0

        # Clip reward to reasonable range
        return max(-100.0, min(100.0, reward))

    async def _store_trajectory(
        self,
        state_hash: str,
        state_data: Dict[str, Any],
        action_id: str,
        reward: float,
        next_state_hash: Optional[str],
        next_state_data: Optional[Dict[str, Any]],
        task_id: str,
        metadata: Dict[str, Any]
    ):
        """Store trajectory (SARS') in database for experience replay

        Args:
            state_hash: Current state hash
            state_data: Current state features
            action_id: Action taken
            reward: Reward received
            next_state_hash: Next state hash (None if terminal)
            next_state_data: Next state features (None if terminal)
            task_id: Task identifier
            metadata: Additional metadata
        """
        if not self.q_service:
            return

        try:
            await self.q_service.store_experience(
                agent_id=self.agent_id,
                state_hash=state_hash,
                state_data=state_data,
                action_id=action_id,
                reward=reward,
                next_state_hash=next_state_hash,
                next_state_data=next_state_data,
                task_id=task_id,
                metadata=metadata
            )
        except Exception as e:
            self.logger.error(f"Failed to store trajectory: {e}", exc_info=True)

    async def _decay_epsilon(self, recent_reward: float):
        """Decay exploration rate (epsilon) based on recent performance

        Uses reward-based epsilon decay (RBED) for adaptive exploration.

        Args:
            recent_reward: Reward from most recent episode
        """
        if not self.q_service:
            return

        try:
            await self.q_service.decay_epsilon(
                agent_id=self.agent_id,
                recent_reward=recent_reward
            )
        except Exception as e:
            self.logger.error(f"Failed to decay epsilon: {e}", exc_info=True)

    def _get_timestamp(self) -> float:
        """Get current timestamp in seconds

        Returns:
            Unix timestamp
        """
        import time
        return time.time()

    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent execution metrics

        Returns:
            Dict of metrics
        """
        return {
            "agent_id": self.agent_id,
            "skills": self.skills,
            **self.metrics,
        }

    async def communicate(
        self,
        instruction: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Simple communication with the agent

        Args:
            instruction: Instruction for the agent
            context: Optional context

        Returns:
            Agent response
        """
        response = await self.branch.communicate(
            instruction=instruction,
            context=context
        )
        return response

    async def operate(
        self,
        instruction: str,
        context: Optional[Dict[str, Any]] = None,
        response_format: Optional[type] = None
    ):
        """Structured operation with Pydantic validation

        Args:
            instruction: Instruction for the agent
            context: Optional context
            response_format: Pydantic model for response

        Returns:
            Structured response
        """
        result = await self.branch.operate(
            instruction=instruction,
            context=context,
            response_format=response_format
        )
        return result

    async def safe_operate(
        self,
        instruction: str,
        response_format: Type[T],
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """Execute operation with fuzzy JSON parsing fallback

        This method provides robust LLM output parsing that handles:
        - Malformed JSON responses
        - Extra text surrounding JSON
        - Key name variations (camelCase vs snake_case)
        - Type coercion for mismatched types
        - Missing or extra fields

        The method first attempts standard LionAGI structured output parsing.
        If that fails, it falls back to fuzzy parsing which is more lenient
        and can extract valid data from messy LLM responses.

        Example:
            ```python
            # Instead of:
            result = await self.branch.operate(
                instruction="Generate test suite",
                response_format=TestSuite
            )

            # Use this for robust parsing:
            result = await self.safe_operate(
                instruction="Generate test suite",
                response_format=TestSuite
            )
            ```

        Args:
            instruction: Instruction for the agent
            response_format: Expected Pydantic model class
            context: Additional context dictionary
            **kwargs: Additional arguments passed to branch.operate()

        Returns:
            Validated Pydantic model instance of type T

        Raises:
            ValueError: If both standard and fuzzy parsing fail

        Note:
            This method reduces parsing errors by 95%+ compared to standard
            parsing, according to migration guide benchmarks.
        """
        try:
            # Try standard LionAGI structured output first
            # This is the fast path for well-formed responses
            result = await self.branch.operate(
                instruction=instruction,
                context=context,
                response_format=response_format,
                **kwargs
            )
            self.logger.debug("Standard parsing successful")
            return result

        except Exception as e:
            self.logger.warning(
                f"Standard parsing failed for {response_format.__name__}: {e}, "
                "attempting fuzzy parsing fallback"
            )

            # Fallback: Get raw response and apply fuzzy parsing
            if not FUZZY_PARSING_AVAILABLE:
                self.logger.error("Fuzzy parsing not available - LionAGI fuzzy module not found")
                raise ValueError(
                    f"Failed to parse LLM response into {response_format.__name__}. "
                    f"Original error: {e}. Fuzzy parsing not available."
                )

            try:
                # Get raw text response without structured parsing
                raw_response = await self.branch.communicate(
                    instruction=instruction,
                    context=context,
                    **kwargs
                )

                # Extract JSON from potentially messy response
                # This handles responses like: "Here's the result: {...} I hope this helps!"
                clean_data = fuzzy_json(raw_response)

                # Fuzzy validate against Pydantic model with lenient matching
                validated = fuzzy_validate_pydantic(
                    clean_data,
                    response_format,
                    fuzzy_match_keys=True,   # Tolerates camelCase vs snake_case
                    fuzzy_match_values=True  # Handles type coercion
                )

                self.logger.info(
                    f"Fuzzy parsing successful for {response_format.__name__}"
                )
                return validated

            except Exception as fuzzy_error:
                self.logger.error(
                    f"Fuzzy parsing also failed for {response_format.__name__}: "
                    f"{fuzzy_error}"
                )
                raise ValueError(
                    f"Failed to parse LLM response into {response_format.__name__}. "
                    f"Standard parsing error: {e}. "
                    f"Fuzzy parsing error: {fuzzy_error}. "
                    f"This may indicate the LLM response was completely invalid."
                )

    async def safe_parse_response(
        self,
        response: Union[str, Dict[str, Any]],
        model_class: Type[T]
    ) -> T:
        """Safely parse any response into a Pydantic model

        This is a utility method for parsing responses that you already have,
        rather than executing a new operation. Useful for:
        - Parsing stored responses from memory
        - Validating external data
        - Re-parsing previously failed responses

        The method attempts direct Pydantic parsing first, then falls back
        to fuzzy parsing if that fails.

        Example:
            ```python
            # Parse a stored response from memory
            stored_response = await self.retrieve_context("previous_result")
            result = await self.safe_parse_response(
                stored_response,
                TestSuite
            )

            # Parse external data
            api_response = get_external_data()
            validated = await self.safe_parse_response(
                api_response,
                CoverageReport
            )
            ```

        Args:
            response: Raw response (string JSON or dict)
            model_class: Pydantic model class to parse into

        Returns:
            Validated Pydantic model instance of type T

        Raises:
            ValueError: If both direct and fuzzy parsing fail

        Note:
            This method is synchronous-safe despite being async. It's async
            to maintain consistency with other agent methods and allow for
            future async enhancements.
        """
        try:
            # Try direct Pydantic parsing first
            if isinstance(response, str):
                # Parse from JSON string
                result = model_class.model_validate_json(response)
            else:
                # Parse from dict
                result = model_class(**response)

            self.logger.debug(f"Direct parsing successful for {model_class.__name__}")
            return result

        except Exception as e:
            self.logger.warning(
                f"Direct parsing failed for {model_class.__name__}: {e}, "
                "attempting fuzzy parsing"
            )

            # Fallback to fuzzy parsing
            if not FUZZY_PARSING_AVAILABLE:
                self.logger.error("Fuzzy parsing not available - LionAGI fuzzy module not found")
                raise ValueError(
                    f"Failed to parse response into {model_class.__name__}. "
                    f"Original error: {e}. Fuzzy parsing not available."
                )

            try:
                # Extract clean data from response
                if isinstance(response, str):
                    clean_data = fuzzy_json(response)
                else:
                    clean_data = response

                # Fuzzy validate with lenient matching
                validated = fuzzy_validate_pydantic(
                    clean_data,
                    model_class,
                    fuzzy_match_keys=True,
                    fuzzy_match_values=True
                )

                self.logger.info(
                    f"Fuzzy parsing successful for {model_class.__name__}"
                )
                return validated

            except Exception as fuzzy_error:
                self.logger.error(
                    f"Fuzzy parsing also failed for {model_class.__name__}: "
                    f"{fuzzy_error}"
                )
                raise ValueError(
                    f"Failed to parse response into {model_class.__name__}. "
                    f"Direct parsing error: {e}. "
                    f"Fuzzy parsing error: {fuzzy_error}"
                )
