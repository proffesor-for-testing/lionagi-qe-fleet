"""QE Fleet orchestration and coordination"""

from typing import List, Dict, Any, Optional
from lionagi import Builder, Session
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
    """

    def __init__(
        self,
        memory: QEMemory,
        router: ModelRouter,
        enable_learning: bool = False
    ):
        """Initialize orchestrator

        Args:
            memory: Shared QE memory instance
            router: Multi-model router
            enable_learning: Enable Q-learning across fleet
        """
        self.memory = memory
        self.router = router
        self.enable_learning = enable_learning

        # Agent registry
        self.agents: Dict[str, BaseQEAgent] = {}

        # LionAGI session for workflow management
        self.session = Session()

        # Logger
        self.logger = logging.getLogger("lionagi_qe.orchestrator")

        # Orchestration metrics
        self.metrics = {
            "workflows_executed": 0,
            "total_agents_used": 0,
            "total_cost": 0.0,
        }

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
        tasks_with_agents = list(zip(agent_ids, tasks))
        results = await alcall(
            tasks_with_agents,
            lambda x: run_agent(x[0], x[1])
        )

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
