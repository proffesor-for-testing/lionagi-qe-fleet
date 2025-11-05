"""Fleet Commander Agent - Hierarchical coordination of QE operations"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask
from lionagi.fields import LIST_INSTRUCT_FIELD_MODEL, Instruct


class TaskDecomposition(BaseModel):
    """Task decomposition result"""

    subtasks: List[Dict[str, Any]] = Field(
        ..., description="List of decomposed subtasks"
    )
    agent_assignments: Dict[str, str] = Field(
        ..., description="Mapping of subtask to agent"
    )
    execution_strategy: str = Field(
        ..., description="Execution strategy (sequential, parallel, hybrid)"
    )
    estimated_duration: float = Field(
        ..., description="Estimated total duration in seconds"
    )


class FleetCommanderAgent(BaseQEAgent):
    """Hierarchical coordinator for 50+ QE agents

    Capabilities:
    - Intelligent task decomposition
    - Agent assignment and coordination
    - Multi-agent workflow orchestration
    - Progress monitoring
    - Result synthesis
    """

    def __init__(
        self,
        agent_id: str,
        model: Any,
        memory: Optional[Any] = None,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional[Any] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize FleetCommander Agent

        Args:
            agent_id: Unique agent identifier
            model: LionAGI model instance
            memory: Memory backend (PostgresMemory/RedisMemory/QEMemory or None for Session.context)
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
            q_learning_service: Optional Q-learning service instance
            memory_config: Optional config for auto-initializing memory backend
        """
        super().__init__(
            agent_id=agent_id,
            model=model,
            memory=memory,
            skills=skills or ['agentic-quality-engineering', 'holistic-testing-pact', 'consultancy-practices'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are the Fleet Commander coordinating QE operations.

**Strategic Responsibilities:**
- Analyze incoming QE requests and requirements
- Decompose complex tasks into manageable subtasks
- Assign subtasks to appropriate specialized agents
- Monitor execution progress across the fleet
- Synthesize results into cohesive reports
- Optimize resource allocation

**Available Specialized Agents:**

Core Testing:
- test-generator: Generate comprehensive test suites
- test-executor: Execute tests across frameworks
- coverage-analyzer: Analyze coverage gaps
- quality-gate: Validate quality metrics
- quality-analyzer: ESLint, SonarQube integration
- code-complexity: Complexity analysis

Performance & Security:
- performance-tester: Load testing (k6, JMeter)
- security-scanner: SAST/DAST scanning

Strategic:
- requirements-validator: Testability analysis
- production-intelligence: Incident replay

Advanced:
- regression-risk-analyzer: ML-powered test selection
- test-data-architect: Test data generation
- api-contract-validator: API contract testing
- flaky-test-hunter: Flaky test detection

Specialized:
- deployment-readiness: Release validation
- visual-tester: Visual regression
- chaos-engineer: Resilience testing

**Coordination Patterns:**
1. Sequential Pipeline: Linear workflow through agents
2. Parallel Fan-out: Multiple agents work simultaneously
3. Hierarchical: Delegate to sub-coordinators
4. Hybrid: Combine strategies based on task complexity

**Decision Criteria:**
- Task complexity and scope
- Agent specialization and capabilities
- Resource availability
- Time constraints
- Quality requirements"""

    async def execute(self, task: QETask) -> Dict[str, Any]:
        """Coordinate multi-agent QE workflow

        Args:
            task: Task containing:
                - request: High-level QE request
                - orchestrator: QEOrchestrator instance
                - available_agents: List of available agents

        Returns:
            Complete workflow result with synthesis
        """
        context = task.context
        request = context.get("request", "")
        orchestrator = context.get("orchestrator")
        available_agents = context.get("available_agents", [])

        # Step 1: Analyze and decompose the request
        decomposition = await self.operate(
            instruct=Instruct(
                instruction=f"""Analyze this QE request and decompose into subtasks:

{request}

Available agents: {', '.join(available_agents)}

Create a detailed execution plan with:
1. Subtasks to execute
2. Agent assignment for each subtask
3. Execution strategy (sequential/parallel/hybrid)
4. Estimated duration

Assign each subtask to the most appropriate specialized agent.
""",
                guidance="Put subtasks into `instruct_model` field with agent assignments in context"
            ),
            field_models=[LIST_INSTRUCT_FIELD_MODEL]
        )

        subtasks = decomposition.instruct_model

        # Step 2: Fan-out to specialized agents
        agent_assignments = [
            st.context.get("agent_id", "test-generator")
            for st in subtasks
        ]

        self.logger.info(
            f"Executing {len(subtasks)} subtasks across agents: "
            f"{', '.join(set(agent_assignments))}"
        )

        # Execute based on strategy
        execution_strategy = context.get("execution_strategy", "parallel")

        if execution_strategy == "parallel" and orchestrator:
            # Execute all in parallel
            results = await orchestrator.execute_parallel(
                agent_assignments,
                [st.to_dict() for st in subtasks]
            )
        elif execution_strategy == "sequential" and orchestrator:
            # Execute sequentially
            result = await orchestrator.execute_pipeline(
                agent_assignments,
                context
            )
            results = [result]
        else:
            # Fallback: simulate execution
            results = [
                {"subtask": st.to_dict(), "status": "simulated"}
                for st in subtasks
            ]

        # Step 3: Synthesize results
        synthesis = await self.communicate(
            instruction="""Synthesize the QE results into a comprehensive report.

Include:
1. Executive summary
2. Key findings from each agent
3. Quality assessment
4. Recommendations
5. Action items
""",
            context={
                "original_request": request,
                "subtasks": [st.to_dict() for st in subtasks],
                "agent_results": results,
            }
        )

        return {
            "original_request": request,
            "decomposition": [st.to_dict() for st in subtasks],
            "agent_assignments": agent_assignments,
            "execution_strategy": execution_strategy,
            "agent_results": results,
            "synthesis": synthesis,
        }
