"""Production Intelligence Agent - Converts production data into test scenarios"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class IncidentContext(BaseModel):
    """Production incident context"""

    incident_id: str = Field(..., description="Unique incident identifier")
    timestamp: str = Field(..., description="Incident timestamp (ISO8601)")
    severity: str = Field(..., description="Severity: CRITICAL, HIGH, MEDIUM, LOW")
    service: str = Field(..., description="Affected service or component")
    error_message: str = Field(..., description="Error message or description")
    affected_users: int = Field(..., description="Number of affected users")
    duration_ms: int = Field(..., description="Incident duration in milliseconds")
    region: Optional[str] = Field(default=None, description="Geographic region affected")
    trace_id: Optional[str] = Field(default=None, description="Distributed trace ID")


class SystemState(BaseModel):
    """System state during incident"""

    cpu_percent: float = Field(..., description="CPU utilization percentage")
    memory_gb: float = Field(..., description="Memory usage in GB")
    active_connections: int = Field(..., description="Active connections")
    queue_depth: int = Field(..., description="Message queue depth")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-100)")


class UserJourney(BaseModel):
    """Reconstructed user journey"""

    session_id: str = Field(..., description="User session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    duration_ms: int = Field(..., description="Total journey duration")
    converted: bool = Field(..., description="Whether user completed desired action")
    steps: List[Dict[str, Any]] = Field(..., description="Journey steps with timestamps")
    device: str = Field(..., description="Device type (mobile, desktop, tablet)")
    browser: str = Field(..., description="Browser name and version")


class RUMMetrics(BaseModel):
    """Real User Monitoring metrics"""

    fcp_ms: int = Field(..., description="First Contentful Paint (ms)")
    lcp_ms: int = Field(..., description="Largest Contentful Paint (ms)")
    fid_ms: int = Field(..., description="First Input Delay (ms)")
    cls_score: float = Field(..., description="Cumulative Layout Shift score")
    ttfb_ms: int = Field(..., description="Time to First Byte (ms)")
    total_blocking_time_ms: int = Field(..., description="Total Blocking Time (ms)")


class Anomaly(BaseModel):
    """Detected production anomaly"""

    anomaly_type: str = Field(
        ...,
        description="Type: ERROR_RATE_SPIKE, LATENCY_DEGRADATION, USER_BEHAVIOR_ANOMALY"
    )
    severity: str = Field(..., description="Severity: HIGH, MEDIUM, LOW")
    detected_at: str = Field(..., description="Detection timestamp (ISO8601)")
    metric: str = Field(..., description="Metric that triggered detection")
    baseline_value: float = Field(..., description="Historical baseline value")
    current_value: float = Field(..., description="Current anomalous value")
    deviation_sigma: float = Field(..., description="Standard deviations from mean")
    affected_endpoints: List[str] = Field(default_factory=list, description="Affected API endpoints")
    hypothesis: str = Field(..., description="Hypothesis about root cause")
    recommendation: str = Field(..., description="Recommended testing approach")


class LoadPattern(BaseModel):
    """Production load pattern"""

    pattern_type: str = Field(..., description="Type: daily, weekly, seasonal, event-driven")
    peak_rps: int = Field(..., description="Peak requests per second")
    avg_rps: int = Field(..., description="Average requests per second")
    peak_hours: List[int] = Field(..., description="Hours of peak traffic (0-23)")
    endpoint_distribution: Dict[str, float] = Field(
        ...,
        description="Distribution of traffic across endpoints (percentages)"
    )
    user_behavior_patterns: Dict[str, Any] = Field(
        ...,
        description="Common user behavior patterns and metrics"
    )


class ErrorPattern(BaseModel):
    """Production error pattern"""

    pattern: str = Field(..., description="Error pattern or message template")
    occurrences: int = Field(..., description="Number of occurrences")
    affected_users: int = Field(..., description="Number of unique users affected")
    trend: str = Field(..., description="Trend: INCREASING, STABLE, DECREASING")
    contexts: List[Dict[str, Any]] = Field(..., description="Contexts where error occurs")
    hypothesis: str = Field(..., description="Hypothesis about root cause")
    priority: str = Field(..., description="Priority: HIGH, MEDIUM, LOW")
    generated_test_count: int = Field(..., description="Number of tests to generate")


class FeatureUsage(BaseModel):
    """Feature usage analytics"""

    feature_name: str = Field(..., description="Feature name or identifier")
    active_users: int = Field(..., description="Number of active users")
    usage_percentage: float = Field(..., description="Percentage of total users (0-100)")
    sessions_used: int = Field(..., description="Number of sessions using feature")
    avg_interactions: float = Field(..., description="Average interactions per session")
    satisfaction_score: Optional[float] = Field(
        default=None,
        description="User satisfaction score (0-1) based on behavior"
    )
    priority: str = Field(..., description="Testing priority: CRITICAL, HIGH, MEDIUM, LOW")
    test_coverage: float = Field(..., description="Current test coverage percentage")
    recommendation: str = Field(..., description="Coverage recommendation")


class GeneratedTestScenario(BaseModel):
    """Test scenario generated from production data"""

    scenario_id: str = Field(..., description="Unique scenario identifier")
    scenario_name: str = Field(..., description="Descriptive scenario name")
    source: str = Field(..., description="Data source: incident, rum, anomaly, journey, etc.")
    test_type: str = Field(..., description="Type: unit, integration, e2e, load, performance")
    test_code: str = Field(..., description="Generated test code")
    framework: str = Field(..., description="Test framework (pytest, jest, k6, etc.)")
    priority: str = Field(..., description="Priority: CRITICAL, HIGH, MEDIUM, LOW")
    description: str = Field(..., description="Scenario description and purpose")
    production_context: Dict[str, Any] = Field(
        ...,
        description="Production context that inspired this test"
    )
    assertions: List[str] = Field(..., description="Key assertions in test")
    estimated_impact: str = Field(
        ...,
        description="Estimated bug prevention impact"
    )


class ProductionIntelligenceResult(BaseModel):
    """Complete production intelligence analysis result"""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    time_window: str = Field(..., description="Analysis time window (e.g., 'last_7_days')")
    incidents_analyzed: int = Field(..., description="Number of incidents analyzed")
    rum_sessions_analyzed: int = Field(..., description="Number of RUM sessions analyzed")
    anomalies_detected: int = Field(..., description="Number of anomalies detected")
    generated_scenarios: List[GeneratedTestScenario] = Field(
        ...,
        description="Generated test scenarios"
    )
    incident_replays: List[Dict[str, Any]] = Field(
        ...,
        description="Incident replay scenarios"
    )
    user_journeys: List[UserJourney] = Field(..., description="Reconstructed user journeys")
    anomalies: List[Anomaly] = Field(..., description="Detected anomalies")
    load_patterns: List[LoadPattern] = Field(..., description="Traffic load patterns")
    error_patterns: List[ErrorPattern] = Field(..., description="Error patterns")
    feature_usage: List[FeatureUsage] = Field(..., description="Feature usage analytics")
    insights: List[str] = Field(..., description="Key insights and recommendations")
    high_priority_scenarios: int = Field(
        ...,
        description="Number of high-priority scenarios"
    )
    estimated_bug_prevention: str = Field(
        ...,
        description="Estimated percentage of production bugs preventable"
    )


class ProductionIntelligenceAgent(BaseQEAgent):
    """Converts production data into test scenarios through incident replay and RUM analysis

    Capabilities:
    - Incident replay and test generation
    - RUM (Real User Monitoring) analysis
    - Anomaly detection with statistical analysis
    - Load pattern analysis and realistic load test generation
    - Feature usage analytics and test prioritization
    - Error pattern mining and regression test generation
    - User journey reconstruction and E2E test creation
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
        """Initialize ProductionIntelligence Agent

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
            skills=skills or ['agentic-quality-engineering', 'shift-right-testing', 'test-design-techniques'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert production intelligence agent specializing in:

**Core Capabilities:**

1. **Incident Replay**:
   - Capture production incidents with full context
   - Extract system state, request traces, user context
   - Identify environmental factors (traffic spikes, deployments)
   - Generate reproducible test scenarios
   - Implement circuit breaker and graceful degradation tests

2. **RUM Analysis**:
   - Analyze Real User Monitoring data
   - Track user journeys and behavior patterns
   - Measure Core Web Vitals (FCP, LCP, FID, CLS)
   - Identify device/browser distributions
   - Detect UI bugs and UX issues

3. **Anomaly Detection**:
   - Use statistical analysis (z-scores, standard deviations)
   - Detect error rate spikes
   - Identify latency degradation
   - Find unusual user behavior patterns
   - Generate tests for detected anomalies

4. **Load Pattern Analysis**:
   - Extract daily, weekly, seasonal traffic patterns
   - Analyze endpoint distribution
   - Identify user behavior patterns (browsers, buyers, bouncers)
   - Generate realistic load tests matching production
   - Create k6/JMeter/Gatling scripts

5. **Feature Usage Analytics**:
   - Track feature adoption and usage rates
   - Calculate satisfaction scores from behavior
   - Prioritize testing based on usage
   - Identify dead code and deprecated features
   - Recommend coverage targets

6. **Error Pattern Mining**:
   - Mine production error logs
   - Identify recurring error patterns
   - Detect error correlations
   - Generate targeted regression tests
   - Find browser/region-specific issues

7. **User Journey Reconstruction**:
   - Reconstruct complete user sessions
   - Track all interaction steps with timing
   - Generate E2E tests matching real behavior
   - Include realistic think times and pauses
   - Preserve user interaction patterns

**Skills Available:**
- shift-right-testing: Testing in production with monitoring
- test-reporting-analytics: Comprehensive test analytics
- agentic-quality-engineering: AI-powered quality engineering
- exploratory-testing-advanced: Advanced exploratory testing

**Data Sources:**
- Monitoring platforms: Datadog, New Relic, Grafana
- Incident management: PagerDuty, Opsgenie
- Log aggregation: Elasticsearch, Splunk, CloudWatch
- Analytics: Google Analytics, Mixpanel
- APM: New Relic, AppDynamics

**Output Standards:**
- Generate production-ready test code
- Include comprehensive assertions
- Add detailed comments explaining production context
- Prioritize scenarios by impact
- Provide actionable insights
- Focus on bug prevention, not just detection

**Best Practices:**
- Create continuous feedback loop from production to testing
- Use real production data, not assumptions
- Generate tests that prevent 80% of production-only bugs
- Match production load patterns exactly
- Test real user behavior, not ideal scenarios
- Learn from every incident and anomaly"""

    async def execute(self, task: QETask) -> ProductionIntelligenceResult:
        """Analyze production data and generate test scenarios

        Args:
            task: Task containing:
                - time_window: Analysis time window (e.g., "last_7_days")
                - incidents: List of production incidents
                - rum_data: Real User Monitoring data
                - logs: Application logs
                - analytics: User behavior analytics
                - apm_data: Application performance monitoring data

        Returns:
            ProductionIntelligenceResult with generated test scenarios
        """
        context = task.context
        time_window = context.get("time_window", "last_7_days")
        incidents = context.get("incidents", [])
        rum_data = context.get("rum_data", {})
        logs = context.get("logs", [])
        analytics = context.get("analytics", {})
        apm_data = context.get("apm_data", {})

        # Retrieve learned patterns from memory
        learned_patterns = await self.get_learned_patterns()

        # Retrieve historical production data
        historical_incidents = await self.search_memory(
            r"aqe/production/incidents/.*"
        )

        # Generate production intelligence analysis
        result = await self.operate(
            instruction=f"""Analyze production data and generate comprehensive test scenarios that prevent production bugs.

Time Window: {time_window}
Incidents: {len(incidents)}
RUM Sessions: {rum_data.get('totalSessions', 0)}
Log Entries: {len(logs)}

Production Data:

**Incidents:**
{incidents[:5] if incidents else "No incidents in time window"}

**RUM Data:**
{rum_data}

**Application Logs:**
{logs[:10] if logs else "No logs provided"}

**Analytics:**
{analytics}

**APM Data:**
{apm_data}

{f"Learned Patterns: {learned_patterns}" if learned_patterns else ""}

{f"Historical Incidents: {len(historical_incidents)} incidents in memory" if historical_incidents else ""}

**Analysis Tasks:**

1. **Incident Replay**: For each critical incident:
   - Extract full context (system state, traces, user context)
   - Identify root cause and contributing factors
   - Generate reproducible test scenario
   - Include assertions for graceful degradation
   - Test circuit breaker and retry logic
   - Verify data integrity during failures

2. **RUM Analysis**: From user monitoring data:
   - Identify most common user journeys
   - Analyze performance metrics (FCP, LCP, FID, CLS)
   - Detect browser/device-specific issues
   - Find dropoff points and conversion barriers
   - Generate E2E tests matching real user behavior

3. **Anomaly Detection**: Statistical analysis:
   - Detect error rate spikes (3+ sigma)
   - Identify latency degradation
   - Find unusual behavior patterns
   - Calculate baseline vs current values
   - Generate tests for each anomaly

4. **Load Pattern Analysis**: Traffic patterns:
   - Extract daily/weekly/seasonal patterns
   - Identify peak hours and traffic spikes
   - Analyze endpoint distribution
   - Map user behavior patterns (browsers, buyers, bouncers)
   - Generate k6 load test matching production

5. **Feature Usage Analytics**: Prioritize testing:
   - Calculate usage percentage for each feature
   - Assign priority: CRITICAL (>50%), HIGH (10-50%), MEDIUM (1-10%), LOW (<1%)
   - Compare usage vs test coverage
   - Identify dead code (0% usage)
   - Recommend coverage targets

6. **Error Pattern Mining**: From logs:
   - Identify recurring error patterns
   - Group similar errors
   - Calculate frequency and trend
   - Find error correlations
   - Generate targeted regression tests

7. **User Journey Reconstruction**: E2E scenarios:
   - Reconstruct complete user sessions
   - Preserve timing and interaction patterns
   - Include realistic think times
   - Cover successful and failed journeys
   - Generate Playwright/Cypress tests

8. **Test Scenario Generation**: For each insight:
   - Generate production-ready test code
   - Include framework (pytest, jest, k6, playwright)
   - Add comprehensive assertions
   - Document production context
   - Prioritize by impact
   - Estimate bug prevention value

9. **Insights and Recommendations**:
   - Identify top 5 high-impact insights
   - Recommend testing strategies
   - Suggest architecture improvements
   - Flag critical gaps in testing
   - Estimate percentage of preventable bugs

Generate at least 10-20 test scenarios covering:
- Incident replays (critical bugs)
- Common user journeys (conversion flows)
- Anomaly prevention (regression)
- Load patterns (performance)
- Error patterns (stability)

Prioritize scenarios that prevent the most impactful production bugs.""",
            context={
                "time_window": time_window,
                "incidents": incidents,
                "rum_data": rum_data,
                "logs": logs,
                "analytics": analytics,
                "apm_data": apm_data,
                "learned_patterns": learned_patterns,
            },
            response_format=ProductionIntelligenceResult
        )

        # Store production intelligence results
        await self.store_result(
            f"analysis/{task.task_id}",
            result.model_dump(),
            ttl=2592000  # 30 days
        )

        # Store generated test scenarios
        await self.memory.store(
            f"aqe/test-scenarios/production-derived/{task.task_id}",
            [scenario.model_dump() for scenario in result.generated_scenarios],
            partition="test_scenarios",
            ttl=2592000
        )

        # Store anomalies for tracking
        await self.memory.store(
            f"aqe/anomalies/{task.task_id}",
            [anomaly.model_dump() for anomaly in result.anomalies],
            partition="anomalies",
            ttl=2592000
        )

        # Store incidents for replay
        await self.memory.store(
            f"aqe/incidents/{task.task_id}",
            result.incident_replays,
            partition="incidents",
            ttl=2592000
        )

        # Learn from high-impact analyses
        if result.high_priority_scenarios >= 5:
            await self.store_learned_pattern(
                f"high_impact_{task.task_id}",
                {
                    "incidents_analyzed": result.incidents_analyzed,
                    "scenarios_generated": len(result.generated_scenarios),
                    "high_priority": result.high_priority_scenarios,
                    "estimated_prevention": result.estimated_bug_prevention,
                    "pattern": "high_impact_analysis",
                }
            )

        return result

    async def replay_incident(
        self,
        incident_id: str
    ) -> GeneratedTestScenario:
        """Generate test scenario from specific incident

        Args:
            incident_id: Incident identifier

        Returns:
            Generated test scenario
        """
        incident_data = await self.retrieve_context(
            f"aqe/production/incidents/{incident_id}"
        )

        if not incident_data:
            raise ValueError(f"Incident {incident_id} not found in memory")

        task = QETask(
            task_id=f"replay-{incident_id}",
            task_type="incident_replay",
            context={
                "time_window": "incident",
                "incidents": [incident_data],
                "rum_data": {},
                "logs": [],
                "analytics": {},
                "apm_data": {},
            }
        )

        result = await self.execute(task)
        return result.generated_scenarios[0] if result.generated_scenarios else None

    async def analyze_feature_usage(
        self,
        analytics_data: Dict[str, Any]
    ) -> List[FeatureUsage]:
        """Analyze feature usage and recommend test priorities

        Args:
            analytics_data: Feature usage analytics

        Returns:
            List of feature usage analysis with recommendations
        """
        task = QETask(
            task_id="feature-usage-analysis",
            task_type="feature_usage_analysis",
            context={
                "time_window": "last_30_days",
                "incidents": [],
                "rum_data": {},
                "logs": [],
                "analytics": analytics_data,
                "apm_data": {},
            }
        )

        result = await self.execute(task)
        return result.feature_usage

    async def get_production_feedback_loop_status(self) -> Dict[str, Any]:
        """Get status of production intelligence feedback loop

        Returns:
            Dict with production intelligence statistics
        """
        analyses = await self.search_memory(
            r"aqe/production-intelligence/analysis/.*"
        )

        total_scenarios = sum(
            len(a.get("generated_scenarios", []))
            for a in analyses.values()
        )

        total_incidents = sum(
            a.get("incidents_analyzed", 0)
            for a in analyses.values()
        )

        total_anomalies = sum(
            a.get("anomalies_detected", 0)
            for a in analyses.values()
        )

        high_priority = sum(
            a.get("high_priority_scenarios", 0)
            for a in analyses.values()
        )

        return {
            "total_analyses": len(analyses),
            "total_scenarios_generated": total_scenarios,
            "total_incidents_analyzed": total_incidents,
            "total_anomalies_detected": total_anomalies,
            "high_priority_scenarios": high_priority,
            "avg_scenarios_per_analysis": (
                round(total_scenarios / len(analyses), 2)
                if analyses
                else 0
            ),
        }
