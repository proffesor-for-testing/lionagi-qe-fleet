"""Performance Tester Agent - Load testing, bottleneck detection, and SLA validation"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class PerformanceMetrics(BaseModel):
    """Performance metrics from load testing"""

    response_time_p50: float = Field(..., description="50th percentile response time (ms)")
    response_time_p95: float = Field(..., description="95th percentile response time (ms)")
    response_time_p99: float = Field(..., description="99th percentile response time (ms)")
    throughput_rps: float = Field(..., description="Requests per second")
    error_rate: float = Field(..., description="Error rate percentage (0-1)")
    availability_percentage: float = Field(..., description="Availability percentage")
    total_requests: int = Field(default=0, description="Total requests executed")
    failed_requests: int = Field(default=0, description="Number of failed requests")


class PerformanceThreshold(BaseModel):
    """Performance thresholds for validation"""

    max_response_time_p95: float = Field(default=500.0, description="Max acceptable P95 response time (ms)")
    min_throughput_rps: float = Field(default=100.0, description="Minimum acceptable RPS")
    max_error_rate: float = Field(default=0.01, description="Maximum acceptable error rate")
    min_availability: float = Field(default=99.9, description="Minimum availability percentage")


class PerformanceBottleneck(BaseModel):
    """Detected performance bottleneck"""

    component: str = Field(..., description="Component with bottleneck")
    metric: str = Field(..., description="Metric indicating bottleneck")
    current_value: float = Field(..., description="Current metric value")
    expected_value: float = Field(..., description="Expected metric value")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    recommendation: str = Field(..., description="Optimization recommendation")


class PerformanceRegression(BaseModel):
    """Detected performance regression"""

    metric: str = Field(..., description="Metric with regression")
    baseline_value: float = Field(..., description="Baseline metric value")
    current_value: float = Field(..., description="Current metric value")
    variance_percentage: float = Field(..., description="Variance percentage")
    threshold_exceeded: bool = Field(..., description="Whether threshold was exceeded")


class PerformanceTestResult(BaseModel):
    """Performance test result"""

    test_name: str = Field(..., description="Name of the performance test")
    tool: str = Field(..., description="Tool used (JMeter, K6, Gatling, etc.)")
    load_pattern: str = Field(..., description="Load pattern (ramp-up, steady, stress)")
    metrics: PerformanceMetrics = Field(..., description="Performance metrics")
    thresholds: PerformanceThreshold = Field(..., description="Performance thresholds")
    bottlenecks: List[PerformanceBottleneck] = Field(default_factory=list, description="Detected bottlenecks")
    regressions: List[PerformanceRegression] = Field(default_factory=list, description="Performance regressions")
    sla_compliant: bool = Field(..., description="Whether SLA was met")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")
    test_duration_seconds: float = Field(..., description="Total test duration")
    virtual_users: int = Field(default=1, description="Number of virtual users")


class PerformanceTesterAgent(BaseQEAgent):
    """Multi-tool performance testing with load orchestration, bottleneck detection, and SLA validation

    Capabilities:
    - Load testing orchestration (JMeter, K6, Gatling, Artillery)
    - Real-time performance monitoring
    - SLA validation and threshold management
    - Bottleneck detection and analysis
    - Performance regression detection
    - Multi-protocol support (HTTP, WebSocket, gRPC, GraphQL)
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
        """Initialize PerformanceTester Agent

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
            skills=skills or ['agentic-quality-engineering', 'performance-testing', 'quality-metrics'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert performance testing agent specializing in:

**Core Capabilities:**
- Load testing orchestration with JMeter, K6, Gatling, Artillery
- Bottleneck detection and root cause analysis
- Resource monitoring (CPU, memory, disk, network)
- SLA validation and compliance checking
- Performance regression detection
- Real-time metrics analysis

**Load Testing Tools:**
- **JMeter**: Distributed load testing, GUI-less execution
- **K6**: JavaScript-based testing, CI/CD integration
- **Gatling**: High-performance Scala-based testing
- **Artillery**: Quick scenario-based load testing
- **Multi-protocol**: HTTP/HTTPS, WebSocket, gRPC, GraphQL

**Performance Monitoring:**
- Response time analysis (P50, P95, P99)
- Throughput and requests per second
- Error rate and availability tracking
- Resource utilization monitoring
- Database query performance
- API endpoint latency

**SLA Validation:**
- Threshold management and validation
- Performance budget enforcement
- Regression detection against baselines
- Automated alerting on violations

**Analysis Capabilities:**
- Identify performance bottlenecks
- Correlate metrics with resource usage
- Provide optimization recommendations
- Generate performance reports
- Trend analysis and forecasting

**Best Practices:**
- Establish baseline metrics before testing
- Use realistic load patterns (ramp-up, steady, stress)
- Monitor system resources during tests
- Validate against defined SLAs
- Provide actionable optimization guidance

**Workflow:**
1. Load baselines and requirements from memory
2. Execute load tests with appropriate patterns
3. Monitor and collect performance metrics
4. Analyze bottlenecks and regressions
5. Validate against SLA thresholds
6. Store results and notify other agents
7. Generate reports with recommendations"""

    async def execute(self, task: QETask) -> PerformanceTestResult:
        """Execute performance testing workflow

        Args:
            task: Task containing:
                - target_url: URL to test
                - tool: Testing tool (jmeter, k6, gatling, artillery)
                - load_pattern: Load pattern (ramp-up, steady, stress)
                - virtual_users: Number of virtual users
                - duration_seconds: Test duration
                - thresholds: Optional performance thresholds

        Returns:
            PerformanceTestResult with metrics, bottlenecks, and recommendations
        """
        context = task.context
        target_url = context.get("target_url", "")
        tool = context.get("tool", "k6")
        load_pattern = context.get("load_pattern", "ramp-up")
        virtual_users = context.get("virtual_users", 100)
        duration_seconds = context.get("duration_seconds", 300)
        custom_thresholds = context.get("thresholds", {})

        # Load baselines from memory
        baselines = await self.memory_store.retrieve(
            "aqe/performance/baselines",
            partition="coordination"
        )

        # Load thresholds from memory or use defaults
        stored_thresholds = await self.memory_store.retrieve(
            "aqe/performance/thresholds",
            partition="coordination"
        )

        # Merge thresholds
        threshold_data = {**(stored_thresholds or {}), **custom_thresholds}

        # Generate performance test
        result = await self.operate(
            instruction=f"""Execute a comprehensive performance test using {tool}.

Target: {target_url}
Load Pattern: {load_pattern}
Virtual Users: {virtual_users}
Duration: {duration_seconds} seconds

Requirements:
1. Execute load test with realistic user patterns
2. Monitor response times (P50, P95, P99)
3. Track throughput and error rates
4. Detect performance bottlenecks
5. Compare against baseline metrics: {baselines if baselines else 'No baseline available'}
6. Validate against SLA thresholds: {threshold_data}
7. Identify performance regressions
8. Provide optimization recommendations

Performance Thresholds:
- P95 Response Time: < {threshold_data.get('max_response_time_p95', 500)}ms
- Throughput: > {threshold_data.get('min_throughput_rps', 100)} RPS
- Error Rate: < {threshold_data.get('max_error_rate', 0.01)}
- Availability: > {threshold_data.get('min_availability', 99.9)}%

Analyze:
- Database query performance
- API endpoint latency
- Resource utilization (CPU, memory)
- Network throughput
- Concurrency handling

Provide specific recommendations for optimization.""",
            context={
                "target_url": target_url,
                "tool": tool,
                "load_pattern": load_pattern,
                "virtual_users": virtual_users,
                "duration_seconds": duration_seconds,
                "baselines": baselines,
                "thresholds": threshold_data,
            },
            response_format=PerformanceTestResult
        )

        # Store results in memory
        await self.memory_store.store(
            "aqe/performance/results",
            {
                "test_name": result.test_name,
                "timestamp": task.created_at.isoformat(),
                "metrics": result.metrics.model_dump(),
                "sla_compliant": result.sla_compliant,
                "tool": result.tool,
            },
            partition="coordination",
            ttl=86400  # 24 hours
        )

        # Store regressions if any
        if result.regressions:
            await self.memory_store.store(
                "aqe/performance/regressions",
                {
                    "test_name": result.test_name,
                    "timestamp": task.created_at.isoformat(),
                    "regressions": [r.model_dump() for r in result.regressions],
                },
                partition="coordination",
                ttl=604800  # 7 days
            )

        # Store as new baseline if test passed and no regressions
        if result.sla_compliant and not result.regressions:
            await self.store_learned_pattern(
                "performance_baseline",
                {
                    "target_url": target_url,
                    "tool": tool,
                    "metrics": result.metrics.model_dump(),
                    "timestamp": task.created_at.isoformat(),
                }
            )

        return result
