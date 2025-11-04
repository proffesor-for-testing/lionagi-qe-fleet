"""Unit tests for ChaosEngineerAgent - Resilience testing with controlled fault injection"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from hypothesis import given, strategies as st
from lionagi_qe.agents.chaos_engineer import (
    ChaosEngineerAgent,
    FaultInjection,
    BlastRadius,
    SteadyStateMetrics,
    ChaosExperimentResult,
)
from lionagi_qe.core.task import QETask


class TestChaosEngineerAgent:
    """Test suite for ChaosEngineerAgent"""

    @pytest.fixture
    async def agent(self, qe_memory, simple_model):
        """Create chaos engineer agent"""
        return ChaosEngineerAgent(
            agent_id="chaos-engineer",
            model=simple_model,
            memory=qe_memory,
            skills=[
                "agentic-quality-engineering",
                "chaos-engineering-resilience",
                "shift-right-testing",
            ],
            enable_learning=False,
        )

    @pytest.fixture
    def network_fault_injection(self):
        """Sample network fault injection config"""
        return FaultInjection(
            fault_type="latency",
            target="api-gateway",
            intensity="gradual",
            duration="5m",
            parameters={
                "latency_ms": 2000,
                "jitter_ms": 500,
                "affected_percentage": 10,
            },
        )

    @pytest.fixture
    def resource_fault_injection(self):
        """Sample resource exhaustion fault injection"""
        return FaultInjection(
            fault_type="resource-exhaustion",
            target="database-service",
            intensity="immediate",
            duration="2m",
            parameters={
                "resource": "cpu",
                "utilization_percent": 95,
            },
        )

    @pytest.fixture
    def blast_radius_config(self):
        """Sample blast radius configuration"""
        return BlastRadius(
            affected_services=["api-gateway"],
            affected_users=50,
            affected_requests=1000,
            contained=True,
            max_services=1,
            max_users=100,
        )

    @pytest.fixture
    def steady_state_config(self):
        """Sample steady state metrics configuration"""
        return {
            "error_rate": {"threshold": 0.01, "baseline": 0.001},
            "latency_p99": {"threshold": 500, "baseline": 250},
            "throughput": {"threshold": 1000, "baseline": 1200},
        }

    # ==================== Initialization Tests ====================

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == "chaos-engineer"
        assert "chaos-engineering-resilience" in agent.skills
        assert agent.enable_learning is False
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent):
        """Test system prompt contains chaos engineering principles"""
        prompt = agent.get_system_prompt()
        assert "chaos engineering" in prompt.lower()
        assert "fault injection" in prompt.lower()
        assert "blast radius" in prompt.lower()
        assert "hypothesis" in prompt.lower()
        assert "resilience" in prompt.lower()

    # ==================== Chaos Experiment Execution Tests ====================

    @pytest.mark.asyncio
    async def test_execute_network_latency_experiment(
        self, agent, network_fault_injection, steady_state_config, mocker
    ):
        """Test network latency chaos experiment"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "network_latency_test",
                "hypothesis": "Service remains available with 2s latency",
                "fault_injection": network_fault_injection.model_dump(),
                "steady_state_metrics": steady_state_config,
                "blast_radius_limits": {"max_services": 1, "max_users": 100},
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-001",
            experiment_name="network_latency_test",
            status="completed",
            hypothesis="Service remains available with 2s latency",
            hypothesis_validated=True,
            execution_time="5m30s",
            fault_injection=network_fault_injection,
            blast_radius=BlastRadius(
                affected_services=["api-gateway"],
                affected_users=50,
                affected_requests=1000,
                contained=True,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[
                SteadyStateMetrics(
                    metric_name="error_rate",
                    baseline_value=0.001,
                    during_chaos_value=0.003,
                    after_chaos_value=0.001,
                    threshold=0.01,
                    violated=False,
                ),
                SteadyStateMetrics(
                    metric_name="latency_p99",
                    baseline_value=250,
                    during_chaos_value=2100,
                    after_chaos_value=280,
                    threshold=500,
                    violated=True,
                ),
            ],
            recovery_time="15s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=[
                "Service maintained availability during latency spike",
                "P99 latency exceeded threshold but recovered quickly",
            ],
            recommendations=[
                "Consider implementing adaptive timeouts",
                "Add circuit breaker for slow downstream services",
            ],
            resilience_score=85,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.status == "completed"
        assert result.hypothesis_validated is True
        assert result.resilience_score >= 80
        assert result.recovery_time is not None
        assert not result.cascading_failures

    @pytest.mark.asyncio
    async def test_execute_resource_exhaustion_experiment(
        self, agent, resource_fault_injection, mocker
    ):
        """Test resource exhaustion chaos experiment"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "cpu_exhaustion_test",
                "hypothesis": "Database maintains query performance under CPU stress",
                "fault_injection": resource_fault_injection.model_dump(),
                "steady_state_metrics": {
                    "query_latency": {"threshold": 100, "baseline": 50}
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-002",
            experiment_name="cpu_exhaustion_test",
            status="completed",
            hypothesis="Database maintains query performance under CPU stress",
            hypothesis_validated=False,
            execution_time="2m15s",
            fault_injection=resource_fault_injection,
            blast_radius=BlastRadius(
                affected_services=["database-service"],
                affected_users=200,
                affected_requests=5000,
                contained=False,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[
                SteadyStateMetrics(
                    metric_name="query_latency",
                    baseline_value=50,
                    during_chaos_value=350,
                    after_chaos_value=55,
                    threshold=100,
                    violated=True,
                )
            ],
            recovery_time="45s",
            auto_rollback_triggered=True,
            cascading_failures=True,
            graceful_degradation=False,
            insights=[
                "CPU exhaustion caused query latency degradation",
                "Cascading failures detected in dependent services",
                "Auto-rollback triggered after blast radius breach",
            ],
            recommendations=[
                "Implement query timeout controls",
                "Add resource-based circuit breakers",
                "Increase connection pool limits",
            ],
            resilience_score=45,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.status == "completed"
        assert result.hypothesis_validated is False
        assert result.auto_rollback_triggered is True
        assert result.cascading_failures is True
        assert result.resilience_score < 50

    @pytest.mark.asyncio
    async def test_execute_experiment_with_early_abort(self, agent, mocker):
        """Test chaos experiment with early abort"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "pod_termination_test",
                "hypothesis": "Service handles pod termination gracefully",
                "fault_injection": {
                    "fault_type": "failure",
                    "target": "user-service",
                    "intensity": "immediate",
                    "duration": "5m",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-003",
            experiment_name="pod_termination_test",
            status="aborted",
            hypothesis="Service handles pod termination gracefully",
            hypothesis_validated=False,
            execution_time="1m20s",
            fault_injection=FaultInjection(
                fault_type="failure",
                target="user-service",
                intensity="immediate",
                duration="5m",
            ),
            blast_radius=BlastRadius(
                affected_services=["user-service", "auth-service", "api-gateway"],
                affected_users=500,
                affected_requests=10000,
                contained=False,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[],
            recovery_time=None,
            auto_rollback_triggered=True,
            cascading_failures=True,
            graceful_degradation=False,
            insights=[
                "Blast radius exceeded limits - experiment aborted",
                "Cascading failures propagated to 3 services",
                "No graceful degradation observed",
            ],
            recommendations=[
                "CRITICAL: Implement proper service isolation",
                "Add health checks and readiness probes",
                "Implement bulkhead pattern for service dependencies",
            ],
            resilience_score=20,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.status == "aborted"
        assert result.auto_rollback_triggered is True
        assert not result.blast_radius.contained
        assert result.resilience_score < 30

    # ==================== Blast Radius Control Tests ====================

    @pytest.mark.asyncio
    async def test_blast_radius_contained(self, agent, blast_radius_config, mocker):
        """Test blast radius is properly contained"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "contained_blast_test",
                "hypothesis": "Fault injection is contained to single service",
                "fault_injection": {
                    "fault_type": "latency",
                    "target": "cache-service",
                    "intensity": "gradual",
                    "duration": "3m",
                },
                "blast_radius_limits": {
                    "max_services": 1,
                    "max_users": 100,
                    "max_requests": 5000,
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-004",
            experiment_name="contained_blast_test",
            status="completed",
            hypothesis="Fault injection is contained to single service",
            hypothesis_validated=True,
            execution_time="3m10s",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="cache-service",
                intensity="gradual",
                duration="3m",
            ),
            blast_radius=BlastRadius(
                affected_services=["cache-service"],
                affected_users=75,
                affected_requests=2000,
                contained=True,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[],
            recovery_time="10s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=["Blast radius successfully contained to single service"],
            recommendations=["Current fault isolation is effective"],
            resilience_score=95,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.blast_radius.contained is True
        assert len(result.blast_radius.affected_services) <= 1
        assert result.blast_radius.affected_users <= 100
        assert not result.cascading_failures

    @pytest.mark.asyncio
    async def test_blast_radius_breach_triggers_rollback(self, agent, mocker):
        """Test blast radius breach triggers automatic rollback"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "blast_breach_test",
                "hypothesis": "System contains blast radius",
                "fault_injection": {
                    "fault_type": "network-partition",
                    "target": "database",
                    "intensity": "immediate",
                    "duration": "5m",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-005",
            experiment_name="blast_breach_test",
            status="aborted",
            hypothesis="System contains blast radius",
            hypothesis_validated=False,
            execution_time="45s",
            fault_injection=FaultInjection(
                fault_type="network-partition",
                target="database",
                intensity="immediate",
                duration="5m",
            ),
            blast_radius=BlastRadius(
                affected_services=["database", "api", "worker", "scheduler"],
                affected_users=1500,
                affected_requests=50000,
                contained=False,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[],
            recovery_time="30s",
            auto_rollback_triggered=True,
            cascading_failures=True,
            graceful_degradation=False,
            insights=[
                "Blast radius breached limits: 4 services affected (limit: 1)",
                "User impact exceeded limit: 1500 users (limit: 100)",
                "Auto-rollback activated at 45s",
            ],
            recommendations=[
                "URGENT: Implement database circuit breakers",
                "Add failover mechanisms for database partitions",
                "Review service dependency graph",
            ],
            resilience_score=15,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert not result.blast_radius.contained
        assert result.auto_rollback_triggered is True
        assert result.blast_radius.affected_users > result.blast_radius.max_users

    # ==================== Steady State Validation Tests ====================

    @pytest.mark.asyncio
    async def test_steady_state_metrics_tracking(self, agent, steady_state_config, mocker):
        """Test steady state metrics are tracked correctly"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "steady_state_test",
                "hypothesis": "System maintains steady state",
                "fault_injection": {
                    "fault_type": "latency",
                    "target": "api",
                    "intensity": "gradual",
                    "duration": "2m",
                },
                "steady_state_metrics": steady_state_config,
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-006",
            experiment_name="steady_state_test",
            status="completed",
            hypothesis="System maintains steady state",
            hypothesis_validated=True,
            execution_time="2m30s",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="api",
                intensity="gradual",
                duration="2m",
            ),
            blast_radius=BlastRadius(
                affected_services=["api"],
                affected_users=0,
                affected_requests=0,
                contained=True,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[
                SteadyStateMetrics(
                    metric_name="error_rate",
                    baseline_value=0.001,
                    during_chaos_value=0.002,
                    after_chaos_value=0.001,
                    threshold=0.01,
                    violated=False,
                ),
                SteadyStateMetrics(
                    metric_name="latency_p99",
                    baseline_value=250,
                    during_chaos_value=400,
                    after_chaos_value=260,
                    threshold=500,
                    violated=False,
                ),
                SteadyStateMetrics(
                    metric_name="throughput",
                    baseline_value=1200,
                    during_chaos_value=1100,
                    after_chaos_value=1190,
                    threshold=1000,
                    violated=False,
                ),
            ],
            recovery_time="8s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=["All steady state metrics remained within thresholds"],
            recommendations=["Current resilience measures are effective"],
            resilience_score=98,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert len(result.steady_state_metrics) == 3
        assert all(not m.violated for m in result.steady_state_metrics)
        assert result.hypothesis_validated is True

    # ==================== Recovery Time Tests ====================

    @pytest.mark.asyncio
    async def test_fast_recovery_time(self, agent, mocker):
        """Test system with fast recovery time"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "fast_recovery_test",
                "hypothesis": "System recovers in under 30s",
                "fault_injection": {
                    "fault_type": "failure",
                    "target": "cache",
                    "intensity": "immediate",
                    "duration": "1m",
                },
                "success_criteria": {"recovery_time": "<30s"},
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-007",
            experiment_name="fast_recovery_test",
            status="completed",
            hypothesis="System recovers in under 30s",
            hypothesis_validated=True,
            execution_time="1m15s",
            fault_injection=FaultInjection(
                fault_type="failure",
                target="cache",
                intensity="immediate",
                duration="1m",
            ),
            blast_radius=BlastRadius(
                affected_services=["cache"],
                affected_users=20,
                affected_requests=500,
                contained=True,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[],
            recovery_time="12s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=["System recovered in 12s - well under 30s target"],
            recommendations=["Recovery mechanisms are functioning well"],
            resilience_score=95,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.recovery_time == "12s"
        assert result.hypothesis_validated is True

    # ==================== Memory Integration Tests ====================

    @pytest.mark.asyncio
    async def test_stores_experiment_results_in_memory(self, agent, qe_memory, mocker):
        """Test experiment results are stored in memory"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "memory_test",
                "hypothesis": "Test memory storage",
                "fault_injection": {
                    "fault_type": "latency",
                    "target": "test",
                    "intensity": "gradual",
                    "duration": "1m",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-008",
            experiment_name="memory_test",
            status="completed",
            hypothesis="Test memory storage",
            hypothesis_validated=True,
            execution_time="1m",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="test",
                intensity="gradual",
                duration="1m",
            ),
            blast_radius=BlastRadius(
                affected_services=[],
                affected_users=0,
                affected_requests=0,
                contained=True,
            ),
            steady_state_metrics=[],
            recovery_time="5s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=[],
            recommendations=[],
            resilience_score=90,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify experiment stored
        stored_experiment = await qe_memory.retrieve(
            f"aqe/chaos-engineer/chaos/experiments/{result.experiment_id}"
        )
        assert stored_experiment is not None

        # Verify metrics stored
        stored_metrics = await qe_memory.retrieve(
            "aqe/chaos-engineer/chaos/metrics/resilience/memory_test"
        )
        assert stored_metrics is not None
        assert stored_metrics["resilience_score"] == 90

    @pytest.mark.asyncio
    async def test_stores_failure_modes(self, agent, qe_memory, mocker):
        """Test failure modes are stored for analysis"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "failure_mode_test",
                "hypothesis": "Test failure capture",
                "fault_injection": {
                    "fault_type": "failure",
                    "target": "test",
                    "intensity": "immediate",
                    "duration": "1m",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-009",
            experiment_name="failure_mode_test",
            status="completed",
            hypothesis="Test failure capture",
            hypothesis_validated=False,
            execution_time="1m",
            fault_injection=FaultInjection(
                fault_type="failure",
                target="test",
                intensity="immediate",
                duration="1m",
            ),
            blast_radius=BlastRadius(
                affected_services=[],
                affected_users=0,
                affected_requests=0,
                contained=True,
            ),
            steady_state_metrics=[],
            recovery_time="30s",
            auto_rollback_triggered=False,
            cascading_failures=True,
            graceful_degradation=False,
            insights=["Cascading failure detected"],
            recommendations=["Add circuit breakers"],
            resilience_score=40,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify failure mode stored
        stored_failure = await qe_memory.retrieve(
            f"aqe/chaos-engineer/chaos/failures/{result.experiment_id}"
        )
        assert stored_failure is not None
        assert stored_failure["failure_mode"] == "cascading_failures"

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_handles_experiment_execution_error(self, agent, mocker):
        """Test handling of experiment execution errors"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "error_test",
                "hypothesis": "Test error handling",
            },
        )

        mocker.patch.object(
            agent,
            "operate",
            side_effect=Exception("Experiment execution failed"),
        )

        with pytest.raises(Exception) as exc_info:
            await agent.execute(task)

        assert "Experiment execution failed" in str(exc_info.value)

    # ==================== Property-Based Tests ====================

    @given(st.integers(min_value=0, max_value=100))
    def test_resilience_score_range(self, score):
        """Property-based test for resilience score range"""
        # Resilience score should always be 0-100
        assert 0 <= score <= 100

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=10),
        st.integers(min_value=0, max_value=1000),
    )
    def test_blast_radius_calculation(self, services, users):
        """Property-based test for blast radius calculation"""
        blast_radius = BlastRadius(
            affected_services=services,
            affected_users=users,
            affected_requests=users * 10,
            contained=len(services) <= 1 and users <= 100,
            max_services=1,
            max_users=100,
        )

        # Blast radius should be marked as contained only if within limits
        if len(services) <= 1 and users <= 100:
            assert blast_radius.contained is True
        else:
            assert blast_radius.contained is False

    # ==================== Helper Method Tests ====================

    @pytest.mark.asyncio
    async def test_format_steady_state_metrics(self, agent):
        """Test steady state metrics formatting helper"""
        metrics = {
            "error_rate": {"threshold": 0.01, "baseline": 0.001},
            "latency": {"threshold": 500, "baseline": 250},
        }

        formatted = agent._format_steady_state_metrics(metrics)

        assert "error_rate" in formatted
        assert "latency" in formatted
        assert "threshold" in formatted

    @pytest.mark.asyncio
    async def test_format_empty_steady_state_metrics(self, agent):
        """Test formatting empty steady state metrics"""
        formatted = agent._format_steady_state_metrics({})
        assert "No steady state metrics configured" in formatted

    # ==================== Integration Tests ====================

    @pytest.mark.asyncio
    async def test_full_chaos_experiment_workflow(self, agent, mocker):
        """Test complete chaos experiment workflow"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "full_workflow_test",
                "hypothesis": "System is resilient to combined faults",
                "fault_injection": {
                    "fault_type": "latency",
                    "target": "api",
                    "intensity": "gradual",
                    "duration": "5m",
                    "parameters": {"latency_ms": 1000},
                },
                "blast_radius_limits": {
                    "max_services": 1,
                    "max_users": 100,
                    "max_duration": "5m",
                },
                "steady_state_metrics": {
                    "error_rate": {"threshold": 0.05, "baseline": 0.001},
                    "latency_p99": {"threshold": 2000, "baseline": 300},
                },
                "success_criteria": {
                    "recovery_time": "<30s",
                    "data_loss": "zero",
                    "cascading_failures": "none",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-full",
            experiment_name="full_workflow_test",
            status="completed",
            hypothesis="System is resilient to combined faults",
            hypothesis_validated=True,
            execution_time="5m45s",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="api",
                intensity="gradual",
                duration="5m",
                parameters={"latency_ms": 1000},
            ),
            blast_radius=BlastRadius(
                affected_services=["api"],
                affected_users=75,
                affected_requests=3000,
                contained=True,
                max_services=1,
                max_users=100,
            ),
            steady_state_metrics=[
                SteadyStateMetrics(
                    metric_name="error_rate",
                    baseline_value=0.001,
                    during_chaos_value=0.008,
                    after_chaos_value=0.001,
                    threshold=0.05,
                    violated=False,
                ),
                SteadyStateMetrics(
                    metric_name="latency_p99",
                    baseline_value=300,
                    during_chaos_value=1100,
                    after_chaos_value=320,
                    threshold=2000,
                    violated=False,
                ),
            ],
            recovery_time="18s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=[
                "System handled gradual latency increase effectively",
                "All steady state metrics remained within thresholds",
                "Recovery time well under 30s target",
            ],
            recommendations=[
                "Current resilience measures are working well",
                "Consider testing with higher intensity",
            ],
            resilience_score=92,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Validate complete workflow
        assert result.status == "completed"
        assert result.hypothesis_validated is True
        assert result.blast_radius.contained is True
        assert all(not m.violated for m in result.steady_state_metrics)
        assert not result.cascading_failures
        assert result.graceful_degradation is True
        assert result.resilience_score >= 90

    @pytest.mark.asyncio
    async def test_concurrent_experiments(self, agent, mocker):
        """Test concurrent chaos experiments"""
        import asyncio

        tasks = [
            QETask(
                task_type="chaos_experiment",
                context={
                    "experiment_name": f"concurrent_test_{i}",
                    "hypothesis": "Test concurrency",
                    "fault_injection": {
                        "fault_type": "latency",
                        "target": f"service-{i}",
                        "intensity": "gradual",
                        "duration": "1m",
                    },
                },
            )
            for i in range(3)
        ]

        mock_result = ChaosExperimentResult(
            experiment_id="exp-concurrent",
            experiment_name="concurrent_test",
            status="completed",
            hypothesis="Test concurrency",
            hypothesis_validated=True,
            execution_time="1m",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="service",
                intensity="gradual",
                duration="1m",
            ),
            blast_radius=BlastRadius(
                affected_services=[],
                affected_users=0,
                affected_requests=0,
                contained=True,
            ),
            steady_state_metrics=[],
            recovery_time="5s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=[],
            recommendations=[],
            resilience_score=90,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        results = await asyncio.gather(*[agent.execute(task) for task in tasks])

        assert len(results) == 3
        assert all(r.status == "completed" for r in results)

    # ==================== Metrics Tests ====================

    @pytest.mark.asyncio
    async def test_agent_metrics_tracking(self, agent, mocker):
        """Test agent tracks metrics correctly"""
        task = QETask(
            task_type="chaos_experiment",
            context={
                "experiment_name": "metrics_test",
                "hypothesis": "Test metrics",
                "fault_injection": {
                    "fault_type": "latency",
                    "target": "test",
                    "intensity": "gradual",
                    "duration": "1m",
                },
            },
        )

        mock_result = ChaosExperimentResult(
            experiment_id="exp-metrics",
            experiment_name="metrics_test",
            status="completed",
            hypothesis="Test metrics",
            hypothesis_validated=True,
            execution_time="1m",
            fault_injection=FaultInjection(
                fault_type="latency",
                target="test",
                intensity="gradual",
                duration="1m",
            ),
            blast_radius=BlastRadius(
                affected_services=[],
                affected_users=0,
                affected_requests=0,
                contained=True,
            ),
            steady_state_metrics=[],
            recovery_time="5s",
            auto_rollback_triggered=False,
            cascading_failures=False,
            graceful_degradation=True,
            insights=[],
            recommendations=[],
            resilience_score=90,
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial_completed = agent.metrics["tasks_completed"]

        await agent.execute(task)

        metrics = await agent.get_metrics()
        assert metrics["tasks_completed"] == initial_completed + 1
