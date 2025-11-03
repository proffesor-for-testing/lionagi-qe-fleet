"""Base class for all QE agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from lionagi import Branch, iModel
from .task import QETask
from .memory import QEMemory
import logging


class BaseQEAgent(ABC):
    """Base class for all QE agents

    All specialized QE agents inherit from this base class and implement:
    - get_system_prompt(): Define agent expertise
    - execute(): Main agent logic

    Agents automatically integrate with:
    - LionAGI Branch for conversations
    - Shared QE memory namespace
    - Multi-model routing
    - Skill registry
    """

    def __init__(
        self,
        agent_id: str,
        model: iModel,
        memory: QEMemory,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False
    ):
        """Initialize QE agent

        Args:
            agent_id: Unique agent identifier (e.g., "test-generator")
            model: LionAGI model instance
            memory: Shared QE memory instance
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
        """
        self.agent_id = agent_id
        self.model = model
        self.memory = memory
        self.skills = skills or []
        self.enable_learning = enable_learning

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
        }

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
        """Q-learning integration (simplified)

        Args:
            task: Completed task
            result: Execution result
        """
        # Store execution trajectory for learning
        trajectory = {
            "task_type": task.task_type,
            "context": task.context,
            "result": result,
            "success": True,
        }

        await self.store_result(
            f"learning/trajectories/{task.task_id}",
            trajectory,
            ttl=2592000,  # 30 days
            partition="learning"
        )

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
