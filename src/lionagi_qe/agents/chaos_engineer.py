"""Chaos Engineer Agent - Resilience testing with controlled fault injection"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class FaultInjection(BaseModel):
    """Fault injection configuration"""

    fault_type: str = Field(
        ...,
        description="Type of fault (latency, failure, resource-exhaustion, network-partition)",
    )
    target: str = Field(..., description="Target service or component")
    intensity: str = Field(..., description="Injection intensity (gradual, immediate, random)")
    duration: str = Field(..., description="Fault duration (e.g., '5m', '30s')")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Fault-specific parameters"
    )


class BlastRadius(BaseModel):
    """Blast radius tracking"""

    affected_services: List[str] = Field(..., description="Services affected by chaos")
    affected_users: int = Field(..., description="Number of users impacted")
    affected_requests: int = Field(..., description="Number of requests impacted")
    contained: bool = Field(..., description="Whether blast radius was contained")
    max_services: int = Field(default=1, description="Maximum allowed affected services")
    max_users: int = Field(default=100, description="Maximum allowed affected users")


class SteadyStateMetrics(BaseModel):
    """System steady state metrics"""

    metric_name: str = Field(..., description="Metric name (error_rate, latency, etc.)")
    baseline_value: float = Field(..., description="Baseline value before chaos")
    during_chaos_value: float = Field(..., description="Value during chaos experiment")
    after_chaos_value: float = Field(..., description="Value after recovery")
    threshold: float = Field(..., description="Acceptable threshold")
    violated: bool = Field(..., description="Whether threshold was violated")


class ChaosExperimentResult(BaseModel):
    """Chaos experiment execution result"""

    experiment_id: str = Field(..., description="Unique experiment identifier")
    experiment_name: str = Field(..., description="Experiment name")
    status: str = Field(..., description="Status (completed, failed, aborted)")
    hypothesis: str = Field(..., description="Hypothesis being tested")
    hypothesis_validated: bool = Field(..., description="Whether hypothesis was validated")
    execution_time: str = Field(..., description="Total execution time")
    fault_injection: FaultInjection = Field(..., description="Fault injection details")
    blast_radius: BlastRadius = Field(..., description="Blast radius impact")
    steady_state_metrics: List[SteadyStateMetrics] = Field(
        ..., description="Steady state metric tracking"
    )
    recovery_time: Optional[str] = Field(None, description="Time to recover from fault")
    auto_rollback_triggered: bool = Field(..., description="Whether auto-rollback was triggered")
    cascading_failures: bool = Field(..., description="Whether cascading failures occurred")
    graceful_degradation: bool = Field(..., description="Whether system degraded gracefully")
    insights: List[str] = Field(default_factory=list, description="Insights from experiment")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improving resilience"
    )
    resilience_score: int = Field(
        ..., description="Overall resilience score (0-100)", ge=0, le=100
    )


class ChaosEngineerAgent(BaseQEAgent):
    """Resilience testing with controlled chaos experiments and fault injection

    Capabilities:
    - Systematic fault injection (network, CPU, memory, disk, application)
    - Recovery testing and failover validation
    - Blast radius control with automatic rollback
    - Experiment orchestration with safety validation
    - Hypothesis-driven chaos experiments
    - Observability integration for metrics correlation
    - Game day scenario execution
    - Progressive chaos with multi-phase experiments

    Skills:
    - agentic-quality-engineering: AI agents as force multipliers
    - chaos-engineering-resilience: Chaos engineering principles and fault injection
    - shift-right-testing: Testing in production with safe practices
    - risk-based-testing: Focus chaos on highest-risk areas
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
        """Initialize ChaosEngineer Agent

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
            skills=skills or ['agentic-quality-engineering', 'chaos-engineering-resilience', 'shift-right-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are a chaos engineering expert specializing in:

**Core Chaos Principles:**
1. Build a hypothesis around steady-state behavior
2. Vary real-world events (failures, latency, resource exhaustion)
3. Run experiments in production with minimal blast radius
4. Automate experiments to run continuously
5. Minimize blast radius with safety constraints

**Fault Injection Techniques:**
- Network Faults: Latency (500ms-5s), packet loss (5-20%), network partition
- Resource Exhaustion: CPU stress (90-95%), memory pressure, disk I/O saturation
- Application Faults: Exception injection, timeout manipulation, response errors
- Infrastructure Faults: Pod/container termination, node failure, zone outage
- Dependency Faults: Database connection pool exhaustion, API rate limiting

**Safety Mechanisms:**
- Pre-flight checks: Verify system in steady state before experiment
- Blast radius limits: Max 1 service, max 100 users, max 5 minutes
- Auto-rollback triggers: Error rate >5%, latency >5s, cascading failures
- Continuous monitoring: Real-time metric collection with 1-second sampling
- Emergency stop: Manual abort with graceful rollback

**Experiment Design:**
1. Define hypothesis (e.g., "Service remains available during database failure")
2. Identify steady-state metrics (error rate <0.1%, p99 latency <500ms)
3. Design fault injection (gradual vs immediate, intensity, duration)
4. Set success criteria (recovery time <30s, zero data loss)
5. Create rollback plan (automated triggers, manual override)

**Chaos Experiment Types:**
- Steady-State Hypothesis Testing: Validate core system behavior
- Game Day Scenarios: Multi-phase disaster recovery exercises
- Progressive Chaos: Escalating fault intensity across phases
- Continuous Chaos: Low-intensity chaos running 24/7 in production

**Observability Integration:**
- System Metrics: CPU, memory, network, disk I/O
- Application Metrics: Request rate, error rate, latency percentiles
- Business Metrics: Active users, transaction rate, revenue impact
- Distributed Tracing: Request flow, cascade depth, retry storms

**Blast Radius Control:**
- Scope: Single service/component isolation
- Duration: Maximum 5 minutes per experiment
- User Impact: Maximum 100 affected users
- Request Impact: Maximum 1000 affected requests
- Environments: Staging, production-canary only

**Rollback Strategy:**
- Automatic triggers: Error rate >5%, p99 latency >5s, cascading failures detected
- Rollback steps: Stop injection → Restore state → Verify recovery
- Max rollback time: <30 seconds
- Escalation: Alert on-call engineer if auto-rollback fails

**Success Criteria:**
- Hypothesis validation: Clear pass/fail based on metrics
- Recovery time: <30 seconds to steady state
- Data loss: Zero data loss or corruption
- Cascading failures: None detected
- Graceful degradation: Partial functionality maintained

**Resilience Scoring:**
- Availability (40% weight): Uptime during chaos
- Recovery Time (30% weight): Speed of recovery
- Blast Radius Control (20% weight): Impact containment
- Graceful Degradation (10% weight): Functionality preservation

**Output Quality:**
- Detailed experiment reports with telemetry
- Root cause analysis for failures
- Actionable remediation recommendations
- Runbook generation for discovered failure modes
- Resilience score trends over time

**Best Practices:**
- Start with staging, gradually move to production
- Run experiments during business hours with team available
- Document all experiments and outcomes
- Learn from failures, iterate on improvements
- Build chaos into CI/CD pipelines"""

    async def execute(self, task: QETask) -> ChaosExperimentResult:
        """Execute chaos experiment

        Args:
            task: Task containing:
                - experiment_name: Name of the chaos experiment
                - hypothesis: Hypothesis being tested
                - fault_injection: Fault injection configuration
                - blast_radius_limits: Maximum allowed impact
                - steady_state_metrics: Metrics to track
                - success_criteria: Criteria for success

        Returns:
            ChaosExperimentResult with experiment outcomes
        """
        await self.pre_execution_hook(task)

        try:
            context = task.context
            experiment_name = context.get("experiment_name", "unknown")
            hypothesis = context.get("hypothesis", "")
            fault_config = context.get("fault_injection", {})
            blast_radius_limits = context.get("blast_radius_limits", {})
            steady_state_config = context.get("steady_state_metrics", {})
            success_criteria = context.get("success_criteria", {})

            # Retrieve experiment queue and safety constraints
            experiment_history = await self.retrieve_context(
                "aqe/chaos/experiments/history"
            )
            safety_rules = await self.retrieve_context("aqe/chaos/safety/constraints")

            # Generate chaos experiment results
            result = await self.operate(
                instruction=f"""Execute chaos engineering experiment: {experiment_name}

**Hypothesis:**
{hypothesis}

**Fault Injection Configuration:**
- Fault Type: {fault_config.get('type', 'unknown')}
- Target: {fault_config.get('target', 'unknown')}
- Intensity: {fault_config.get('intensity', 'gradual')}
- Duration: {fault_config.get('duration', '5m')}
- Parameters: {fault_config.get('parameters', {})}

**Blast Radius Limits:**
- Max Services: {blast_radius_limits.get('max_services', 1)}
- Max Users: {blast_radius_limits.get('max_users', 100)}
- Max Duration: {blast_radius_limits.get('max_duration', '5m')}

**Steady State Metrics to Track:**
{self._format_steady_state_metrics(steady_state_config)}

**Success Criteria:**
- Recovery Time: {success_criteria.get('recovery_time', '<30s')}
- Data Loss: {success_criteria.get('data_loss', 'zero')}
- Cascading Failures: {success_criteria.get('cascading_failures', 'none')}

**Experiment Execution Steps:**
1. Pre-flight safety checks:
   - Verify system in steady state (error rate <0.01, latency normal)
   - Validate blast radius limits are configured
   - Confirm rollback plan is ready
   - Check on-call availability

2. Baseline collection (1 minute):
   - Collect steady state metrics before chaos
   - Establish baseline error rate, latency, throughput

3. Fault injection:
   - Execute {fault_config.get('intensity', 'gradual')} fault injection
   - Monitor blast radius in real-time (10-second intervals)
   - Track steady state metric deviations

4. Observability:
   - Collect system metrics (CPU, memory, network)
   - Collect application metrics (requests, errors, latency)
   - Capture distributed traces
   - Monitor for cascading failures

5. Auto-rollback triggers:
   - Error rate >5% for 1 minute
   - p99 latency >5000ms for 1 minute
   - Cascading failures detected
   - Blast radius limit breached

6. Recovery validation:
   - Measure time to return to steady state
   - Verify zero data loss or corruption
   - Confirm no permanent degradation

7. Analysis:
   - Validate hypothesis (pass/fail)
   - Calculate recovery time
   - Assess blast radius containment
   - Evaluate graceful degradation
   - Generate insights and recommendations

**Resilience Scoring Breakdown:**
- Availability (40%): Did service remain available during chaos?
- Recovery Time (30%): How quickly did system recover?
- Blast Radius Control (20%): Was impact contained within limits?
- Graceful Degradation (10%): Did system degrade gracefully?

Provide comprehensive experiment results with actionable insights.""",
                response_format=ChaosExperimentResult,
            )

            # Store experiment results in memory
            await self.store_result(
                f"chaos/experiments/{result.experiment_id}",
                result.model_dump(),
                ttl=2592000,  # 30 days
            )

            # Store resilience metrics
            await self.store_result(
                f"chaos/metrics/resilience/{experiment_name}",
                {
                    "resilience_score": result.resilience_score,
                    "recovery_time": result.recovery_time,
                    "hypothesis_validated": result.hypothesis_validated,
                },
                ttl=2592000,
            )

            # Store discovered failure modes
            if not result.hypothesis_validated or result.cascading_failures:
                await self.store_result(
                    f"chaos/failures/{result.experiment_id}",
                    {
                        "experiment": experiment_name,
                        "failure_mode": "hypothesis_failed"
                        if not result.hypothesis_validated
                        else "cascading_failures",
                        "insights": result.insights,
                        "recommendations": result.recommendations,
                    },
                    ttl=2592000,
                )

            await self.post_execution_hook(task, result.model_dump())
            return result

        except Exception as e:
            await self.error_handler(task, e)
            raise

    def _format_steady_state_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format steady state metrics for prompt"""
        if not metrics:
            return "No steady state metrics configured"

        formatted = []
        for metric, config in metrics.items():
            threshold = config.get("threshold", "unknown")
            formatted.append(f"  - {metric}: threshold {threshold}")

        return "\n".join(formatted)

    async def validate_experiment_safety(
        self, experiment_config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate experiment safety before execution

        Args:
            experiment_config: Experiment configuration

        Returns:
            Safety check results
        """
        # This would contain safety validation logic
        pass

    async def execute_fault_injection(
        self, fault_config: FaultInjection
    ) -> Dict[str, Any]:
        """Execute fault injection

        Args:
            fault_config: Fault injection configuration

        Returns:
            Injection execution results
        """
        # This would contain actual fault injection logic
        pass

    async def monitor_blast_radius(
        self, limits: BlastRadius
    ) -> Dict[str, Any]:
        """Monitor blast radius in real-time

        Args:
            limits: Blast radius limits

        Returns:
            Current blast radius status
        """
        # This would contain blast radius monitoring logic
        pass
