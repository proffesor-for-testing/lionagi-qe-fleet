"""Main QE Fleet interface"""

from typing import Dict, Any, List, Optional
from .memory import QEMemory
from .router import ModelRouter
from .orchestrator import QEOrchestrator
from .task import QETask
from .base_agent import BaseQEAgent
import logging


class QEFleet:
    """Main interface for LionAGI QE Fleet

    Provides high-level API for:
    - Fleet initialization
    - Agent registration
    - Task execution
    - Workflow orchestration
    """

    def __init__(
        self,
        enable_routing: bool = True,
        enable_learning: bool = False
    ):
        """Initialize QE Fleet

        Args:
            enable_routing: Enable multi-model routing for cost optimization
            enable_learning: Enable Q-learning across fleet
        """
        # Core components
        self.memory = QEMemory()
        self.router = ModelRouter(enable_routing=enable_routing)
        self.orchestrator = QEOrchestrator(
            memory=self.memory,
            router=self.router,
            enable_learning=enable_learning
        )

        # Configuration
        self.enable_routing = enable_routing
        self.enable_learning = enable_learning

        # Fleet state
        self.initialized = False

        # Logger
        self.logger = logging.getLogger("lionagi_qe.fleet")

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

    async def get_agent(self, agent_id: str) -> Optional[BaseQEAgent]:
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
