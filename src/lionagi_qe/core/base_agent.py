"""Base class for all QE agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from lionagi import Branch, iModel
from .task import QETask
from .memory import QEMemory
import logging

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
