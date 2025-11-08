"""QE Fleet orchestration and coordination"""

from typing import List, Dict, Any, Optional, Callable, Union
from lionagi import Builder, Session
from lionagi.operations import ExpansionStrategy
from .base_agent import BaseQEAgent
from .memory import QEMemory
from .router import ModelRouter
from .task import QETask
import logging


class QEOrchestrator:
    """Orchestrate QE agent workflows

    Handles:
    - Agent registration and lifecycle
    - Sequential pipeline execution
    - Parallel multi-agent execution
    - Workflow graph building
    - Session management
    - Environment-based storage mode selection

    Storage Modes:
        - DEV: Session.context (zero setup, in-memory)
        - TEST: Session.context (isolated, fast tests)
        - PROD: PostgresMemory (durable, ACID guarantees)

    Usage:
        # Option 1: Auto-detect from environment
        orchestrator = QEOrchestrator.from_environment()

        # Option 2: Explicit mode
        orchestrator = QEOrchestrator(mode="production", database_url="postgresql://...")

        # Option 3: Traditional (backward compatible)
        memory = QEMemory()
        router = ModelRouter()
        orchestrator = QEOrchestrator(memory=memory, router=router)
    """

    def __init__(
        self,
        memory: Optional[QEMemory] = None,
        router: Optional[ModelRouter] = None,
        enable_learning: bool = False,
        mode: Optional[Union[str, "StorageMode"]] = None,
        database_url: Optional[str] = None,
        storage_config: Optional["StorageConfig"] = None
    ):
        """Initialize orchestrator

        Args:
            memory: Shared QE memory instance (None = auto-detect from mode)
            router: Multi-model router (None = create default)
            enable_learning: Enable Q-learning across fleet
            mode: Storage mode (dev/test/prod) - auto-detects if not provided
            database_url: PostgreSQL URL (required for prod mode)
            storage_config: StorageConfig instance (overrides mode/database_url)

        Examples:
            # Development (default)
            orchestrator = QEOrchestrator()

            # Testing
            orchestrator = QEOrchestrator(mode="test")

            # Production
            orchestrator = QEOrchestrator(
                mode="prod",
                database_url="postgresql://user:pass@localhost:5432/db"
            )

            # From config
            config = StorageConfig.from_environment()
            orchestrator = QEOrchestrator.from_config(config)
        """
        # Initialize storage configuration
        if storage_config:
            self.storage_config = storage_config
        elif mode or database_url:
            # Create config from parameters
            from ..config import StorageMode, StorageConfig

            if isinstance(mode, str):
                mode = StorageMode.from_string(mode)
            elif mode is None:
                mode = StorageMode.DEV

            self.storage_config = StorageConfig(
                mode=mode,
                database_url=database_url
            )
        elif memory is None:
            # No explicit config or memory - auto-detect from environment
            from ..config import StorageConfig
            self.storage_config = StorageConfig.from_environment()
        else:
            # Legacy mode - memory provided directly
            self.storage_config = None

        # LionAGI session for workflow management (must be created before memory initialization)
        self.session = Session()

        # Logger (must be created before memory initialization)
        self.logger = logging.getLogger("lionagi_qe.orchestrator")

        # Initialize memory backend
        if memory is not None:
            # Legacy: explicit memory provided
            self.memory = memory
        elif self.storage_config:
            # Modern: auto-initialize from config
            self.memory = self._initialize_memory_from_config()
        else:
            # Fallback: default QEMemory
            self.memory = QEMemory()

        # Initialize router
        self.router = router or ModelRouter()
        self.enable_learning = enable_learning

        # Agent registry
        self.agents: Dict[str, BaseQEAgent] = {}

        # Log configuration
        if self.storage_config:
            self.logger.info(
                f"QEOrchestrator initialized with storage mode: "
                f"{self.storage_config.mode.value}"
            )
            self.logger.debug(
                f"Storage configuration:\n{self.storage_config.get_description()}"
            )
        else:
            self.logger.info("QEOrchestrator initialized with custom memory backend")

        # Orchestration metrics
        self.metrics = {
            "workflows_executed": 0,
            "total_agents_used": 0,
            "total_cost": 0.0,
            "parallel_expansions": 0,
            "items_processed": 0,
            "fan_out_fan_in_executed": 0,
            "conditional_workflows": 0,
        }

    def _initialize_memory_from_config(self) -> Any:
        """Initialize memory backend from storage configuration

        Returns:
            Memory backend instance based on configuration

        Raises:
            ValueError: If configuration is invalid
        """
        from ..config import StorageMode

        if self.storage_config.mode in (StorageMode.DEV, StorageMode.TEST):
            # Use QEMemory (in-memory) - Session.context is not available in current lionagi version
            from .memory import QEMemory
            self.logger.info("Using QEMemory for in-memory storage")
            return QEMemory()

        elif self.storage_config.mode == StorageMode.PROD:
            # Use PostgresMemory
            try:
                from ..learning import DatabaseManager
                from ..persistence import PostgresMemory
            except ImportError as e:
                raise ImportError(
                    "Production mode requires lionagi-qe-fleet package with PostgreSQL support. "
                    "Install with: pip install lionagi-qe-fleet"
                ) from e

            self.logger.info(
                f"Initializing PostgresMemory with database: "
                f"{self.storage_config._extract_host_from_url(self.storage_config.database_url)}"
            )

            # Create database manager
            self.db_manager = DatabaseManager(
                database_url=self.storage_config.database_url,
                min_connections=self.storage_config.min_connections,
                max_connections=self.storage_config.max_connections,
                connection_timeout=self.storage_config.connection_timeout,
                pool_recycle=self.storage_config.pool_recycle
            )

            # Note: Connection must be established by caller using connect()
            # This keeps __init__ synchronous
            self.logger.info(
                "DatabaseManager created. Call orchestrator.connect() to establish connection."
            )

            return PostgresMemory(self.db_manager)

        else:
            raise ValueError(f"Unknown storage mode: {self.storage_config.mode}")

    @classmethod
    def from_environment(cls, enable_learning: bool = False) -> "QEOrchestrator":
        """Create orchestrator by auto-detecting environment

        Reads environment variables to determine storage mode:
        - AQE_STORAGE_MODE, ENVIRONMENT, NODE_ENV
        - DATABASE_URL (for production)
        - Connection pool settings

        Args:
            enable_learning: Enable Q-learning across fleet

        Returns:
            QEOrchestrator configured for current environment

        Example:
            ```bash
            # Development (default)
            export ENVIRONMENT=development
            orchestrator = QEOrchestrator.from_environment()

            # Production
            export ENVIRONMENT=production
            export DATABASE_URL=postgresql://user:pass@localhost:5432/db
            orchestrator = QEOrchestrator.from_environment()
            await orchestrator.connect()
            ```
        """
        from ..config import StorageConfig

        config = StorageConfig.from_environment()
        return cls.from_config(config, enable_learning=enable_learning)

    @classmethod
    def from_config(
        cls,
        config: "StorageConfig",
        enable_learning: bool = False
    ) -> "QEOrchestrator":
        """Create orchestrator from storage configuration

        Args:
            config: StorageConfig instance
            enable_learning: Enable Q-learning across fleet

        Returns:
            QEOrchestrator configured according to config

        Example:
            ```python
            from lionagi_qe.config import StorageConfig

            # Development
            config = StorageConfig.for_development()
            orchestrator = QEOrchestrator.from_config(config)

            # Production
            config = StorageConfig.for_production(
                database_url="postgresql://..."
            )
            orchestrator = QEOrchestrator.from_config(config)
            await orchestrator.connect()
            ```
        """
        return cls(
            storage_config=config,
            enable_learning=enable_learning
        )

    async def connect(self):
        """Connect to storage backend (required for production mode)

        For production mode with PostgreSQL, this establishes the database
        connection pool. For dev/test modes, this is a no-op.

        Example:
            ```python
            orchestrator = QEOrchestrator(mode="prod", database_url="postgresql://...")
            await orchestrator.connect()
            # Now ready to use
            ```
        """
        if hasattr(self, 'db_manager'):
            self.logger.info("Connecting to PostgreSQL database...")
            await self.db_manager.connect()
            self.logger.info("Database connection established")
        else:
            self.logger.debug("No database connection required for current mode")

    async def disconnect(self):
        """Disconnect from storage backend

        Cleanly closes database connections and releases resources.

        Example:
            ```python
            try:
                await orchestrator.connect()
                # ... use orchestrator ...
            finally:
                await orchestrator.disconnect()
            ```
        """
        if hasattr(self, 'db_manager'):
            self.logger.info("Closing database connections...")
            await self.db_manager.close()
            self.logger.info("Database connections closed")
        else:
            self.logger.debug("No database connection to close")

    def get_memory_config_for_agents(self) -> Dict[str, Any]:
        """Get memory configuration for registering agents

        Returns configuration dict suitable for passing to BaseQEAgent's
        memory_config parameter when registering agents.

        Returns:
            Dict with memory backend configuration

        Example:
            ```python
            orchestrator = QEOrchestrator.from_environment()
            memory_config = orchestrator.get_memory_config_for_agents()

            agent = TestGeneratorAgent(
                agent_id="test-gen",
                model=model,
                memory_config=memory_config
            )
            orchestrator.register_agent(agent)
            ```
        """
        if self.storage_config:
            return self.storage_config.get_memory_backend_config()
        else:
            # Legacy mode - agents will use provided memory directly
            return {"type": "custom"}

    def create_and_register_agent(
        self,
        agent_class: type[BaseQEAgent],
        agent_id: str,
        model: Any,
        **kwargs
    ) -> BaseQEAgent:
        """Create an agent with shared memory backend and register it

        This is a convenience method that creates an agent with the orchestrator's
        memory backend configuration and immediately registers it.

        Args:
            agent_class: Agent class to instantiate (e.g., TestGeneratorAgent)
            agent_id: Unique agent identifier
            model: LionAGI model instance
            **kwargs: Additional arguments passed to agent constructor

        Returns:
            Created and registered agent instance

        Example:
            ```python
            from lionagi_qe.agents import TestGeneratorAgent, CoverageAnalyzerAgent

            orchestrator = QEOrchestrator.from_environment()
            await orchestrator.connect()

            # Create agents with shared memory backend
            test_gen = orchestrator.create_and_register_agent(
                TestGeneratorAgent,
                agent_id="test-generator",
                model=model
            )

            coverage = orchestrator.create_and_register_agent(
                CoverageAnalyzerAgent,
                agent_id="coverage-analyzer",
                model=model
            )

            # Agents automatically share the same memory backend
            ```
        """
        # Get memory config if not explicitly provided
        if "memory" not in kwargs and "memory_config" not in kwargs:
            # Pass memory backend directly for efficiency
            kwargs["memory"] = self.memory

        # Create agent
        agent = agent_class(
            agent_id=agent_id,
            model=model,
            **kwargs
        )

        # Register
        self.register_agent(agent)

        return agent

    def register_agent(self, agent: BaseQEAgent):
        """Register a QE agent

        Args:
            agent: QE agent instance
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")

    def get_agent(self, agent_id: str) -> Optional[BaseQEAgent]:
        """Get registered agent by ID

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)

    async def execute_agent(
        self,
        agent_id: str,
        task: QETask
    ) -> Dict[str, Any]:
        """Execute a single agent

        Args:
            agent_id: ID of agent to execute
            task: Task to execute

        Returns:
            Task execution result
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        try:
            # Mark task in progress
            task.mark_in_progress(agent_id)

            # Pre-execution hook
            await agent.pre_execution_hook(task)

            # Execute task
            result = await agent.execute(task)

            # Post-execution hook
            await agent.post_execution_hook(task, result)

            # Mark task completed
            task.mark_completed(result)

            return result

        except Exception as e:
            # Handle error
            await agent.error_handler(task, e)
            task.mark_failed(str(e))
            raise

    async def execute_pipeline(
        self,
        pipeline: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a sequential QE pipeline

        Args:
            pipeline: List of agent IDs in execution order
            context: Shared context for all agents

        Returns:
            Dict containing all operation results

        Example:
            pipeline = [
                "test-generator",
                "test-executor",
                "coverage-analyzer",
                "quality-gate"
            ]
        """
        self.logger.info(f"Executing pipeline: {' → '.join(pipeline)}")

        builder = Builder(f"QE_Pipeline_{len(pipeline)}_agents")
        nodes = []

        # Build workflow graph
        for i, agent_id in enumerate(pipeline):
            agent = self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found in pipeline: {agent_id}")

            # Create operation node
            node = builder.add_operation(
                "communicate",
                depends_on=nodes[-1:] if nodes else [],  # Depend on previous
                branch=agent.branch,
                instruction=context.get("instruction", f"Execute {agent_id}"),
                context=context
            )
            nodes.append(node)

        # Execute workflow
        result = await self.session.flow(builder.get_graph())

        self.metrics["workflows_executed"] += 1
        self.metrics["total_agents_used"] += len(pipeline)

        return result

    async def execute_parallel(
        self,
        agent_ids: List[str],
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple agents in parallel

        Args:
            agent_ids: List of agent IDs to execute
            tasks: List of task contexts (one per agent)

        Returns:
            List of execution results

        Example:
            results = await orchestrator.execute_parallel(
                agent_ids=["test-generator", "security-scanner", "performance-tester"],
                tasks=[
                    {"code": code1},
                    {"path": "./src"},
                    {"endpoint": "/api/users"}
                ]
            )
        """
        from lionagi.ln import alcall

        self.logger.info(f"Executing {len(agent_ids)} agents in parallel")

        async def run_agent(agent_id: str, task_context: Dict[str, Any]):
            agent = self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")

            task = QETask(
                task_type=task_context.get("task_type", "execute"),
                context=task_context
            )

            return await self.execute_agent(agent_id, task)

        # Execute all agents in parallel
        import asyncio
        tasks_with_agents = list(zip(agent_ids, tasks))
        coroutines = [run_agent(agent_id, task_ctx) for agent_id, task_ctx in tasks_with_agents]
        results = await asyncio.gather(*coroutines)

        self.metrics["total_agents_used"] += len(agent_ids)

        return results

    async def execute_fan_out_fan_in(
        self,
        coordinator_agent: str,
        worker_agents: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute fan-out/fan-in pattern

        Args:
            coordinator_agent: ID of coordinator agent
            worker_agents: List of worker agent IDs
            context: Initial context

        Returns:
            Final synthesis result

        Workflow:
            1. Coordinator analyzes and decomposes task
            2. Fan-out: Workers execute subtasks in parallel
            3. Fan-in: Coordinator synthesizes results
        """
        from lionagi.fields import LIST_INSTRUCT_FIELD_MODEL, Instruct

        self.logger.info(
            f"Fan-out/fan-in: {coordinator_agent} → "
            f"{len(worker_agents)} workers"
        )

        coordinator = self.get_agent(coordinator_agent)
        if not coordinator:
            raise ValueError(f"Coordinator not found: {coordinator_agent}")

        # Step 1: Coordinator decomposes task
        decomposition = await coordinator.operate(
            instruct=Instruct(
                instruction="Decompose this QE task into parallel subtasks",
                context=context,
                guidance=(
                    f"Create {len(worker_agents)} subtasks, "
                    "one for each worker agent"
                )
            ),
            field_models=[LIST_INSTRUCT_FIELD_MODEL]
        )

        subtasks = decomposition.instruct_model

        # Step 2: Fan-out - execute workers in parallel
        worker_results = await self.execute_parallel(
            worker_agents,
            [st.to_dict() for st in subtasks]
        )

        # Step 3: Fan-in - coordinator synthesizes
        synthesis = await coordinator.communicate(
            instruction="Synthesize QE results into final report",
            context={
                "subtasks": subtasks,
                "worker_results": worker_results
            }
        )

        return {
            "decomposition": [st.to_dict() for st in subtasks],
            "worker_results": worker_results,
            "synthesis": synthesis
        }

    async def execute_hierarchical(
        self,
        fleet_commander: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute hierarchical coordination

        Args:
            fleet_commander: ID of fleet commander agent
            context: Task context

        Returns:
            Hierarchical execution result

        The fleet commander will:
        1. Analyze the request
        2. Assign to appropriate specialized agents
        3. Monitor and coordinate execution
        4. Synthesize results
        """
        commander = self.get_agent(fleet_commander)
        if not commander:
            raise ValueError(f"Fleet commander not found: {fleet_commander}")

        task = QETask(
            task_type="hierarchical_coordination",
            context={
                **context,
                "orchestrator": self,  # Pass orchestrator for agent spawning
                "available_agents": list(self.agents.keys())
            }
        )

        result = await self.execute_agent(fleet_commander, task)
        return result

    async def execute_parallel_expansion(
        self,
        source_agent_id: str,
        target_agent_id: str,
        expansion_instruction: str,
        strategy: ExpansionStrategy = ExpansionStrategy.CONCURRENT,
        max_concurrent: int = 10,
        aggregate_results: bool = True
    ) -> Dict[str, Any]:
        """
        Execute source agent, then expand results in parallel with target agent

        This implements the parallel fan-out pattern where a source agent produces
        a list of items, and a target agent processes each item in parallel using
        LionAGI's ExpansionStrategy.

        Args:
            source_agent_id: Agent that produces list of items to expand
            target_agent_id: Agent that processes each item in parallel
            expansion_instruction: Template instruction (use {{item}} placeholder)
            strategy: Expansion strategy (CONCURRENT, SEQUENTIAL, etc.)
            max_concurrent: Maximum parallel operations
            aggregate_results: Whether to aggregate results at end

        Returns:
            Dictionary containing:
                - source_result: Result from source agent
                - expanded_results: List of results from parallel execution
                - aggregated_result: Synthesized result (if aggregate_results=True)

        Example:
            # Analyze code → Generate tests for each module in parallel
            result = await orchestrator.execute_parallel_expansion(
                source_agent_id="code-analyzer",
                target_agent_id="test-generator",
                expansion_instruction="Generate comprehensive tests for module: {{item}}",
                strategy=ExpansionStrategy.CONCURRENT,
                max_concurrent=10
            )

        Performance:
            - 5-10x faster than sequential processing
            - Automatic retry and error handling via alcall
            - Configurable concurrency limits
        """
        self.logger.info(
            f"Parallel expansion: {source_agent_id} → {target_agent_id} "
            f"(strategy: {strategy}, max_concurrent: {max_concurrent})"
        )

        builder = Builder("parallel-expansion")

        # Step 1: Source operation
        source_agent = self.get_agent(source_agent_id)
        if not source_agent:
            raise ValueError(f"Source agent not found: {source_agent_id}")

        source_op = builder.add_operation(
            "communicate",
            branch=source_agent.branch,
            instruction="Analyze and identify items for parallel processing"
        )

        # Step 2: Parallel expansion
        target_agent = self.get_agent(target_agent_id)
        if not target_agent:
            raise ValueError(f"Target agent not found: {target_agent_id}")

        expanded_ops = builder.expand_from_result(
            items=source_op.response.items,  # LionAGI extracts list automatically
            source_node_id=source_op,
            operation="communicate",
            branch=target_agent.branch,
            strategy=strategy,
            instruction=expansion_instruction,
            max_concurrent=max_concurrent,
            inherit_context=True  # Automatically passes context from source
        )

        # Step 3: Optional aggregation
        aggregation_op = None
        if aggregate_results:
            aggregation_op = builder.add_aggregation(
                "communicate",
                branch=source_agent.branch,  # Use source agent for synthesis
                source_node_ids=expanded_ops,
                instruction="Synthesize all results into comprehensive report",
                context={"original_request": source_op.context}
            )

        # Execute workflow
        result = await self.session.flow(
            builder.get_graph(),
            max_concurrent=max_concurrent
        )

        # Track metrics
        self.metrics["parallel_expansions"] += 1
        self.metrics["items_processed"] += len(expanded_ops)
        self.metrics["workflows_executed"] += 1

        return {
            "source_result": result.get(source_op.id),
            "expanded_results": [result.get(op.id) for op in expanded_ops],
            "aggregated_result": result.get(aggregation_op.id) if aggregation_op else None
        }

    async def execute_parallel_fan_out_fan_in(
        self,
        agent_ids: List[str],
        shared_context: Dict[str, Any],
        synthesis_agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fan-out to multiple agents in parallel, fan-in to synthesis

        This implements the parallel fan-out/fan-in pattern where multiple agents execute
        in parallel with the same context, and their results are synthesized by
        a coordinator agent. This uses LionAGI's Builder for graph-based orchestration.

        Args:
            agent_ids: List of agent IDs to execute in parallel
            shared_context: Context shared across all parallel agents
            synthesis_agent_id: Agent to synthesize results (defaults to first agent)

        Returns:
            Dictionary containing:
                - individual_results: Results from each agent (keyed by agent_id)
                - synthesis: Synthesized result from coordinator

        Example:
            # Run security, performance, quality checks in parallel → synthesize
            result = await orchestrator.execute_parallel_fan_out_fan_in(
                agent_ids=["security-scanner", "performance-tester", "quality-analyzer"],
                shared_context={"code_path": "./src"},
                synthesis_agent_id="fleet-commander"
            )

        Use Cases:
            - Multi-dimensional analysis (security + performance + quality)
            - Parallel test execution with result aggregation
            - Distributed scanning with centralized reporting
        """
        self.logger.info(
            f"Fan-out/fan-in: {len(agent_ids)} agents → synthesis "
            f"(synthesis: {synthesis_agent_id or agent_ids[0]})"
        )

        builder = Builder("fan-out-fan-in")

        # Fan-out: Execute all agents in parallel
        agent_ops = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")

            op = builder.add_operation(
                "communicate",
                branch=agent.branch,
                instruction=f"{agent_id} analysis",
                context=shared_context
            )
            agent_ops.append(op)

        # Fan-in: Synthesize results
        synthesis_agent = self.get_agent(synthesis_agent_id or agent_ids[0])
        if not synthesis_agent:
            raise ValueError(
                f"Synthesis agent not found: {synthesis_agent_id or agent_ids[0]}"
            )

        synthesis_op = builder.add_aggregation(
            "communicate",
            branch=synthesis_agent.branch,
            source_node_ids=agent_ops,
            instruction="Synthesize all expert analyses into actionable recommendations"
        )

        # Execute
        result = await self.session.flow(
            builder.get_graph(),
            max_concurrent=len(agent_ids)
        )

        # Track metrics
        self.metrics["fan_out_fan_in_executed"] += 1
        self.metrics["total_agents_used"] += len(agent_ids)
        self.metrics["workflows_executed"] += 1

        return {
            "individual_results": {
                agent_id: result.get(op.id)
                for agent_id, op in zip(agent_ids, agent_ops)
            },
            "synthesis": result.get(synthesis_op.id)
        }

    async def execute_conditional_workflow(
        self,
        agent_id: str,
        task: Dict[str, Any],
        decision_key: str,
        branches: Dict[str, List[str]],
        decision_fn: Optional[Callable[[Any], str]] = None
    ) -> Dict[str, Any]:
        """
        Execute conditional workflow based on agent output

        This implements conditional branching where the workflow path is determined
        dynamically based on the output of an initial agent. Different agent
        pipelines execute based on the decision.

        Args:
            agent_id: Initial agent to execute
            task: Task context for initial agent
            decision_key: Key in result to use for branching decision
            branches: Map of branch names to agent pipelines
            decision_fn: Optional function to map result value to branch name
                        If not provided, uses simple equality check

        Returns:
            Dictionary containing:
                - initial_result: Result from initial agent
                - branch_taken: Name of branch that was executed
                - branch_results: Results from the executed branch pipeline

        Example:
            # Run coverage analyzer → if coverage < 80%, generate more tests
            result = await orchestrator.execute_conditional_workflow(
                agent_id="coverage-analyzer",
                task={"code_path": "./src"},
                decision_key="coverage_percent",
                branches={
                    "high": ["quality-gate"],  # coverage >= 80%
                    "low": ["test-generator", "test-executor", "coverage-analyzer"]
                },
                decision_fn=lambda cov: "high" if cov >= 80 else "low"
            )

        Use Cases:
            - Quality gates with remediation workflows
            - Adaptive testing based on coverage
            - Security severity-based escalation
            - Performance threshold-based optimization
        """
        self.logger.info(
            f"Conditional workflow: {agent_id} → "
            f"branches: {list(branches.keys())}"
        )

        builder = Builder("conditional-workflow")

        # Initial operation
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        initial_op = builder.add_operation(
            "communicate",
            branch=agent.branch,
            instruction=task.get("instruction", "Execute task"),
            context=task
        )

        # Execute initial operation to get decision value
        initial_result = await self.session.flow(builder.get_graph())
        decision_value = initial_result.get(initial_op.id, {}).get(decision_key)

        # Determine which branch to take
        if decision_fn:
            branch_name = decision_fn(decision_value)
        else:
            # Default: find first branch that matches
            branch_name = None
            for name, _ in branches.items():
                if str(decision_value) == name or decision_value in name:
                    branch_name = name
                    break

            if not branch_name:
                raise ValueError(
                    f"No matching branch for decision value: {decision_value}. "
                    f"Available branches: {list(branches.keys())}"
                )

        self.logger.info(
            f"Conditional decision: {decision_key}={decision_value} → "
            f"branch '{branch_name}'"
        )

        # Execute the selected branch pipeline
        pipeline = branches[branch_name]
        if pipeline:
            branch_result = await self.execute_pipeline(
                pipeline=pipeline,
                context={
                    **task,
                    "initial_result": initial_result,
                    "decision_value": decision_value
                }
            )
        else:
            branch_result = None

        # Track metrics
        self.metrics["conditional_workflows"] += 1
        self.metrics["workflows_executed"] += 1
        self.metrics["total_agents_used"] += 1 + len(pipeline) if pipeline else 1

        return {
            "initial_result": initial_result.get(initial_op.id),
            "branch_taken": branch_name,
            "decision_value": decision_value,
            "branch_results": branch_result
        }

    async def get_fleet_status(self) -> Dict[str, Any]:
        """Get fleet status and metrics

        Returns:
            Fleet status including agent metrics
        """
        agent_statuses = {}

        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = await agent.get_metrics()

        routing_stats = await self.router.get_routing_stats()

        return {
            "total_agents": len(self.agents),
            "agent_statuses": agent_statuses,
            "orchestration_metrics": self.metrics,
            "routing_stats": routing_stats,
            "memory_stats": await self.memory.get_stats()
        }
