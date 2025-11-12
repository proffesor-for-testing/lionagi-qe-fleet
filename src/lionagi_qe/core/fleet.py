"""Main QE Fleet interface

DEPRECATED: This module is deprecated as of v1.1.0 and will be removed in v2.0.0.
Please use QEOrchestrator directly instead.
See docs/migration/fleet-to-orchestrator.md for migration guide.
"""

import warnings
from typing import Dict, Any, List, Optional, Callable
from lionagi.operations import ExpansionStrategy
from .memory import QEMemory
from .router import ModelRouter
from .orchestrator import QEOrchestrator
from .task import QETask
from .base_agent import BaseQEAgent
from .hooks import QEHooks
import logging


class QEFleet:
    """Main interface for LionAGI QE Fleet

    DEPRECATED: This class is deprecated as of v1.1.0 and will be removed in v2.0.0.

    Migration guide:
        Before:
            fleet = QEFleet(enable_routing=True)
            await fleet.initialize()
            fleet.register_agent(agent)
            result = await fleet.execute(agent_id, task)

        After:
            from lionagi_qe import QEOrchestrator, ModelRouter
            from lionagi.core import Session

            memory = Session().context  # or QEMemory() for now
            router = ModelRouter(enable_routing=True)
            orchestrator = QEOrchestrator(memory, router)
            orchestrator.register_agent(agent)
            result = await orchestrator.execute_agent(agent_id, task)

    See docs/migration/fleet-to-orchestrator.md for detailed migration guide.

    Provides high-level API for:
    - Fleet initialization
    - Agent registration
    - Task execution
    - Workflow orchestration
    """

    def __init__(
        self,
        enable_routing: bool = True,
        enable_learning: bool = False,
        enable_hooks: bool = True,
        fleet_id: str = "qe-fleet",
        cost_alert_threshold: float = 10.0
    ):
        """Initialize QE Fleet

        DEPRECATED: Use QEOrchestrator instead.

        Args:
            enable_routing: Enable multi-model routing for cost optimization
            enable_learning: Enable Q-learning across fleet
            enable_hooks: Enable observability hooks for cost/metric tracking
            fleet_id: Unique identifier for this fleet instance
            cost_alert_threshold: Dollar amount that triggers cost warnings
        """
        warnings.warn(
            "QEFleet is deprecated and will be removed in v2.0.0. "
            "Use QEOrchestrator instead. "
            "See docs/migration/fleet-to-orchestrator.md for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )
        # Initialize hooks first (if enabled)
        self.hooks = QEHooks(
            fleet_id=fleet_id,
            cost_alert_threshold=cost_alert_threshold
        ) if enable_hooks else None

        # Core components
        self.memory = QEMemory()
        self.router = ModelRouter(
            enable_routing=enable_routing,
            hooks=self.hooks
        )
        self.orchestrator = QEOrchestrator(
            memory=self.memory,
            router=self.router,
            enable_learning=enable_learning
        )

        # Configuration
        self.enable_routing = enable_routing
        self.enable_learning = enable_learning
        self.enable_hooks = enable_hooks
        self.fleet_id = fleet_id

        # Fleet state
        self.initialized = False

        # Logger
        self.logger = logging.getLogger(f"lionagi_qe.fleet.{fleet_id}")

    async def initialize(self):
        """Initialize the fleet

        This is where you would:
        - Load agent definitions
        - Register agents
        - Setup integrations
        - Restore state from persistence
        """
        if self.initialized:
            self.logger.warning("Fleet already initialized")
            return

        self.logger.info("Initializing LionAGI QE Fleet...")

        # Initialize core components
        self.logger.info("✓ Memory namespace initialized")
        self.logger.info(f"✓ Multi-model router initialized (enabled: {self.enable_routing})")
        self.logger.info("✓ Orchestrator initialized")

        # Note: Agents are registered separately via register_agent()
        # This allows for flexible agent composition

        self.initialized = True
        self.logger.info("Fleet initialization complete")

    def register_agent(self, agent: BaseQEAgent):
        """Register an agent with the fleet

        Args:
            agent: QE agent instance to register
        """
        self.orchestrator.register_agent(agent)
        self.logger.info(f"Registered agent: {agent.agent_id}")

    async def execute(
        self,
        agent_id: str,
        task: QETask
    ) -> Dict[str, Any]:
        """Execute a single agent task

        Args:
            agent_id: ID of agent to execute
            task: Task to execute

        Returns:
            Task execution result
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_agent(agent_id, task)

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
            Pipeline execution results

        Example:
            result = await fleet.execute_pipeline(
                pipeline=[
                    "test-generator",
                    "test-executor",
                    "coverage-analyzer",
                    "quality-gate"
                ],
                context={
                    "code_path": "./src",
                    "framework": "pytest",
                    "coverage_threshold": 80
                }
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_pipeline(pipeline, context)

    async def execute_parallel(
        self,
        agents: List[str],
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple agents in parallel

        Args:
            agents: List of agent IDs
            tasks: List of task contexts

        Returns:
            List of execution results

        Example:
            results = await fleet.execute_parallel(
                agents=["test-generator", "security-scanner", "performance-tester"],
                tasks=[
                    {"code": code, "framework": "pytest"},
                    {"path": "./src", "scan_type": "sast"},
                    {"endpoint": "/api/users", "duration": 60}
                ]
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_parallel(agents, tasks)

    async def execute_fan_out_fan_in(
        self,
        coordinator: str,
        workers: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute fan-out/fan-in workflow pattern

        Args:
            coordinator: Coordinator agent ID
            workers: List of worker agent IDs
            context: Initial context

        Returns:
            Workflow execution result with synthesis

        Example:
            result = await fleet.execute_fan_out_fan_in(
                coordinator="fleet-commander",
                workers=["test-generator", "security-scanner", "performance-tester"],
                context={"project_path": "./", "target": "production"}
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_fan_out_fan_in(
            coordinator, workers, context
        )

    async def execute_workflow(self, workflow_graph):
        """Execute a custom workflow graph

        Args:
            workflow_graph: LionAGI Builder graph

        Returns:
            Workflow execution result
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.session.flow(workflow_graph)

    async def parallel_expansion(
        self,
        source_agent: str,
        target_agent: str,
        instruction: str,
        strategy: ExpansionStrategy = ExpansionStrategy.CONCURRENT,
        max_concurrent: int = 10,
        aggregate_results: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience method for parallel expansion pattern

        Execute source agent to get a list of items, then process each item
        in parallel with target agent.

        Args:
            source_agent: Agent that produces list of items
            target_agent: Agent that processes each item
            instruction: Template instruction (use {{item}} placeholder)
            strategy: Expansion strategy (default: CONCURRENT)
            max_concurrent: Maximum parallel operations
            aggregate_results: Whether to aggregate results at end

        Returns:
            Dictionary with source_result, expanded_results, and aggregated_result

        Example:
            result = await fleet.parallel_expansion(
                source_agent="code-analyzer",
                target_agent="test-generator",
                instruction="Generate comprehensive tests for module: {{item}}",
                max_concurrent=10
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_parallel_expansion(
            source_agent_id=source_agent,
            target_agent_id=target_agent,
            expansion_instruction=instruction,
            strategy=strategy,
            max_concurrent=max_concurrent,
            aggregate_results=aggregate_results
        )

    async def fan_out_fan_in(
        self,
        agents: List[str],
        context: Dict[str, Any],
        synthesis_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for fan-out/fan-in pattern

        Execute multiple agents in parallel with shared context, then synthesize
        their results with a coordinator agent.

        Args:
            agents: List of agent IDs to execute in parallel
            context: Shared context for all agents
            synthesis_agent: Agent to synthesize results (defaults to first agent)

        Returns:
            Dictionary with individual_results and synthesis

        Example:
            result = await fleet.fan_out_fan_in(
                agents=["security-scanner", "performance-tester", "quality-analyzer"],
                context={"code_path": "./src"},
                synthesis_agent="fleet-commander"
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_parallel_fan_out_fan_in(
            agent_ids=agents,
            shared_context=context,
            synthesis_agent_id=synthesis_agent
        )

    async def conditional_workflow(
        self,
        agent: str,
        task: Dict[str, Any],
        decision_key: str,
        branches: Dict[str, List[str]],
        decision_fn: Optional[Callable[[Any], str]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for conditional workflow pattern

        Execute initial agent, then branch to different pipelines based on
        the result value.

        Args:
            agent: Initial agent to execute
            task: Task context for initial agent
            decision_key: Key in result to use for branching
            branches: Map of branch names to agent pipelines
            decision_fn: Optional function to map result value to branch name

        Returns:
            Dictionary with initial_result, branch_taken, and branch_results

        Example:
            result = await fleet.conditional_workflow(
                agent="coverage-analyzer",
                task={"code_path": "./src"},
                decision_key="coverage_percent",
                branches={
                    "high": ["quality-gate"],
                    "low": ["test-generator", "test-executor", "coverage-analyzer"]
                },
                decision_fn=lambda cov: "high" if cov >= 80 else "low"
            )
        """
        if not self.initialized:
            await self.initialize()

        return await self.orchestrator.execute_conditional_workflow(
            agent_id=agent,
            task=task,
            decision_key=decision_key,
            branches=branches,
            decision_fn=decision_fn
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get fleet status and metrics

        Returns:
            Complete fleet status including:
            - Agent statuses
            - Memory statistics
            - Routing statistics
            - Orchestration metrics
        """
        if not self.initialized:
            return {"status": "not_initialized"}

        return await self.orchestrator.get_fleet_status()

    def get_agent(self, agent_id: str) -> Optional[BaseQEAgent]:
        """Get registered agent by ID

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None
        """
        return self.orchestrator.get_agent(agent_id)

    async def export_state(self) -> Dict[str, Any]:
        """Export complete fleet state

        Returns:
            Exportable fleet state for persistence
        """
        return {
            "memory": await self.memory.export_state(),
            "router_stats": await self.router.get_routing_stats(),
            "orchestrator_metrics": self.orchestrator.metrics,
        }

    async def import_state(self, state: Dict[str, Any]):
        """Import fleet state from export

        Args:
            state: Exported fleet state
        """
        await self.memory.import_state(state.get("memory", {}))
        self.logger.info("Fleet state imported")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive fleet metrics including hooks data

        Returns:
            Dictionary containing:
            - Hook metrics (AI call costs, tokens, timing)
            - Router statistics (model selection, cost savings)
            - Orchestrator metrics (task execution)
            - Memory statistics (usage, cache hits)

        Example:
            >>> fleet = QEFleet(enable_hooks=True)
            >>> # ... execute some tasks ...
            >>> metrics = fleet.get_metrics()
            >>> print(f"Total AI cost: ${metrics['hooks']['total_cost']:.2f}")
            >>> print(f"Total calls: {metrics['hooks']['total_calls']}")
        """
        metrics = {
            "fleet_id": self.fleet_id,
            "configuration": {
                "routing_enabled": self.enable_routing,
                "learning_enabled": self.enable_learning,
                "hooks_enabled": self.enable_hooks
            }
        }

        # Add hook metrics if enabled
        if self.hooks:
            metrics["hooks"] = self.hooks.get_metrics()
        else:
            metrics["hooks"] = {
                "enabled": False,
                "message": "Hooks are disabled. Enable with enable_hooks=True"
            }

        # Add router stats
        # Note: get_routing_stats is async, so we can't call it here
        # Users should call await fleet.export_state() for full async stats
        metrics["router"] = {
            "enabled": self.enable_routing,
            "note": "Use await fleet.export_state() for detailed routing stats"
        }

        # Add orchestrator metrics
        if hasattr(self.orchestrator, 'metrics'):
            metrics["orchestrator"] = self.orchestrator.metrics
        else:
            metrics["orchestrator"] = {"message": "No metrics available"}

        return metrics

    def get_call_count(self) -> int:
        """Get total number of AI model calls made by the fleet

        Returns:
            Number of AI model invocations tracked by hooks

        Raises:
            RuntimeError: If hooks are not enabled

        Example:
            >>> fleet = QEFleet(enable_hooks=True)
            >>> # ... execute some tasks ...
            >>> print(f"Total AI calls: {fleet.get_call_count()}")
        """
        if not self.hooks:
            raise RuntimeError(
                "Hooks are not enabled. Initialize fleet with enable_hooks=True "
                "to track AI call counts."
            )

        return self.hooks.get_call_count()

    def get_cost_summary(self) -> str:
        """Get human-readable cost summary

        Returns:
            Formatted string with cost breakdown

        Example:
            >>> print(fleet.get_cost_summary())
        """
        if not self.hooks:
            return "Hooks disabled - no cost tracking available"

        return self.hooks.export_metrics(format="summary")

    def get_dashboard(self) -> str:
        """Get ASCII dashboard of current metrics

        Returns:
            ASCII art dashboard with key metrics

        Example:
            >>> print(fleet.get_dashboard())
        """
        if not self.hooks:
            return "Hooks disabled - no dashboard available"

        return self.hooks.dashboard_ascii()

    def export_hooks_metrics(self, format: str = "json") -> str:
        """Export hook metrics in specified format

        Args:
            format: Export format ('json', 'csv', 'summary')

        Returns:
            Formatted metrics string

        Example:
            >>> metrics_json = fleet.export_hooks_metrics(format="json")
            >>> with open("metrics.json", "w") as f:
            ...     f.write(metrics_json)
        """
        if not self.hooks:
            return '{"error": "Hooks disabled"}'

        return self.hooks.export_metrics(format=format)

    def reset_metrics(self):
        """Reset all hook metrics to zero

        Useful for starting a new measurement period.

        Example:
            >>> fleet.reset_metrics()
            >>> # Start new test run
        """
        if self.hooks:
            self.hooks.reset_metrics()
            self.logger.info("Fleet metrics reset")
        else:
            self.logger.warning("Cannot reset metrics - hooks are disabled")
