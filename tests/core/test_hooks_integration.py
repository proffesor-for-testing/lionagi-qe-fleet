"""Tests for QE Fleet hooks integration

This module tests the observability system including:
- Hook attachment to models
- Cost tracking
- Call counting
- Metrics aggregation
- Alert triggering
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.lionagi_qe.core.hooks import QEHooks
from src.lionagi_qe.core.router import ModelRouter
from src.lionagi_qe.core.fleet import QEFleet


class TestQEHooks:
    """Test suite for QEHooks class"""

    def test_initialization(self):
        """Test hooks initialization"""
        hooks = QEHooks(fleet_id="test-fleet", cost_alert_threshold=5.0)

        assert hooks.fleet_id == "test-fleet"
        assert hooks.cost_alert_threshold == 5.0
        assert hooks.call_count == 0
        assert hooks.cost_tracker["total"] == 0.0
        assert len(hooks.cost_tracker["by_agent"]) == 0

    def test_create_registry(self):
        """Test hook registry creation"""
        hooks = QEHooks(fleet_id="test")
        registry = hooks.create_registry()

        assert registry is not None
        # Registry should have pre and post invocation hooks
        assert hasattr(registry, 'hooks')

    @pytest.mark.asyncio
    async def test_pre_invocation_hook(self):
        """Test pre-invocation hook logging"""
        hooks = QEHooks(fleet_id="test", enable_detailed_logging=True)

        # Mock event
        event = Mock()
        event.provider = "openai"
        event.model = "gpt-4"

        context = {
            "agent_id": "test-agent",
            "task_type": "test-generation"
        }

        await hooks.pre_invocation_hook(event, context=context)

        assert hooks.call_count == 1
        assert len(hooks.call_history) == 1
        assert hooks.call_history[0]["agent_id"] == "test-agent"
        assert hooks.call_history[0]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_post_invocation_hook_with_cost(self):
        """Test post-invocation hook with cost tracking"""
        hooks = QEHooks(fleet_id="test")

        # Mock event with usage
        event = Mock()
        event.provider = "openai"
        event.model = "gpt-4"

        usage = Mock()
        usage.prompt_tokens = 100
        usage.completion_tokens = 50
        usage.total_tokens = 150
        usage.total_cost = 0.0045  # $0.0045

        event.usage = usage

        context = {
            "agent_id": "test-agent"
        }

        # Add a call to history first
        hooks.call_count = 1
        hooks.call_history.append({
            "call_number": 1,
            "phase": "pre_invocation"
        })

        await hooks.post_invocation_hook(event, context=context)

        # Verify cost tracking
        assert hooks.cost_tracker["total"] == 0.0045
        assert "test-agent" in hooks.cost_tracker["by_agent"]
        assert hooks.cost_tracker["by_agent"]["test-agent"]["total_cost"] == 0.0045
        assert hooks.cost_tracker["by_agent"]["test-agent"]["call_count"] == 1

        # Verify token tracking
        assert hooks.token_usage["total_input_tokens"] == 100
        assert hooks.token_usage["total_output_tokens"] == 50
        assert hooks.token_usage["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_post_invocation_hook_estimates_cost(self):
        """Test post-invocation hook estimates cost when not provided"""
        hooks = QEHooks(fleet_id="test")

        # Mock event with usage but no cost
        event = Mock()
        event.provider = "openai"
        event.model = "gpt-3.5-turbo"

        usage = Mock()
        usage.prompt_tokens = 1000
        usage.completion_tokens = 500
        usage.total_tokens = 1500
        usage.total_cost = None  # No cost provided

        event.usage = usage

        context = {"agent_id": "test-agent"}

        hooks.call_count = 1
        hooks.call_history.append({"call_number": 1, "phase": "pre_invocation"})

        await hooks.post_invocation_hook(event, context=context)

        # Should have estimated cost (not zero)
        assert hooks.cost_tracker["total"] > 0

    def test_cost_estimation(self):
        """Test cost estimation logic"""
        hooks = QEHooks(fleet_id="test")

        # Test GPT-3.5 pricing
        cost_gpt35 = hooks._estimate_cost("openai", "gpt-3.5-turbo", 1000, 500)
        assert cost_gpt35 > 0
        assert cost_gpt35 < 0.01  # Should be very cheap

        # Test GPT-4 pricing
        cost_gpt4 = hooks._estimate_cost("openai", "gpt-4", 1000, 500)
        assert cost_gpt4 > cost_gpt35  # GPT-4 should be more expensive

        # Test Claude pricing
        cost_claude = hooks._estimate_cost(
            "anthropic", "claude-3-5-sonnet-20241022", 1000, 500
        )
        assert cost_claude > 0

    @pytest.mark.asyncio
    async def test_cost_alert_triggering(self):
        """Test cost alert when threshold exceeded"""
        hooks = QEHooks(fleet_id="test", cost_alert_threshold=0.01)

        # Mock high-cost call
        event = Mock()
        event.provider = "openai"
        event.model = "gpt-4"

        usage = Mock()
        usage.prompt_tokens = 10000
        usage.completion_tokens = 5000
        usage.total_tokens = 15000
        usage.total_cost = 0.05  # $0.05 - exceeds $0.01 threshold

        event.usage = usage

        context = {"agent_id": "expensive-agent"}

        hooks.call_count = 1
        hooks.call_history.append({"call_number": 1, "phase": "pre_invocation"})

        await hooks.post_invocation_hook(event, context=context)

        # Alert should be triggered
        assert len(hooks.alerts_triggered) == 1
        assert hooks.alerts_triggered[0]["total_cost"] >= hooks.cost_alert_threshold

    def test_get_metrics(self):
        """Test metrics retrieval"""
        hooks = QEHooks(fleet_id="test-fleet")
        hooks.call_count = 10
        hooks.cost_tracker["total"] = 0.05
        hooks.token_usage["total_tokens"] = 15000

        metrics = hooks.get_metrics()

        assert metrics["fleet_id"] == "test-fleet"
        assert metrics["total_calls"] == 10
        assert metrics["total_cost"] == 0.05
        assert metrics["token_usage"]["total_tokens"] == 15000
        assert metrics["average_cost_per_call"] == 0.005
        assert metrics["average_tokens_per_call"] == 1500

    def test_get_call_count(self):
        """Test call count retrieval"""
        hooks = QEHooks(fleet_id="test")
        hooks.call_count = 42

        assert hooks.get_call_count() == 42

    def test_get_agent_metrics(self):
        """Test agent-specific metrics"""
        hooks = QEHooks(fleet_id="test")
        hooks.cost_tracker["by_agent"]["test-agent"] = {
            "total_cost": 0.10,
            "call_count": 5,
            "total_tokens": 7500
        }

        agent_metrics = hooks.get_agent_metrics("test-agent")

        assert agent_metrics is not None
        assert agent_metrics["total_cost"] == 0.10
        assert agent_metrics["call_count"] == 5

    def test_export_metrics_json(self):
        """Test JSON metrics export"""
        hooks = QEHooks(fleet_id="test")
        hooks.call_count = 5
        hooks.cost_tracker["total"] = 0.025

        json_output = hooks.export_metrics(format="json")

        assert isinstance(json_output, str)
        assert "fleet_id" in json_output
        assert "test" in json_output
        assert "0.025" in json_output

    def test_export_metrics_summary(self):
        """Test summary metrics export"""
        hooks = QEHooks(fleet_id="test")
        hooks.call_count = 5
        hooks.cost_tracker["total"] = 0.025
        hooks.cost_tracker["by_agent"]["agent1"] = {
            "total_cost": 0.015,
            "call_count": 3,
            "total_tokens": 4500
        }

        summary = hooks.export_metrics(format="summary")

        assert isinstance(summary, str)
        assert "QE Fleet Metrics Summary" in summary
        assert "Total Cost:" in summary
        assert "agent1" in summary

    def test_reset_metrics(self):
        """Test metrics reset"""
        hooks = QEHooks(fleet_id="test")
        hooks.call_count = 10
        hooks.cost_tracker["total"] = 0.50
        hooks.token_usage["total_tokens"] = 50000

        hooks.reset_metrics()

        assert hooks.call_count == 0
        assert hooks.cost_tracker["total"] == 0.0
        assert hooks.token_usage["total_tokens"] == 0
        assert len(hooks.call_history) == 0

    def test_dashboard_ascii(self):
        """Test ASCII dashboard generation"""
        hooks = QEHooks(fleet_id="test-fleet")
        hooks.call_count = 10
        hooks.cost_tracker["total"] = 0.123

        dashboard = hooks.dashboard_ascii()

        assert isinstance(dashboard, str)
        assert "QE Fleet Observability Dashboard" in dashboard
        assert "test-fleet" in dashboard
        assert "Total Cost:" in dashboard


class TestModelRouterHooksIntegration:
    """Test suite for ModelRouter with hooks"""

    def test_router_initialization_with_hooks(self):
        """Test router initialization with hooks"""
        hooks = QEHooks(fleet_id="test")
        router = ModelRouter(enable_routing=True, hooks=hooks)

        assert router.hooks is hooks
        # All models should have hook registry attached
        # Note: We can't directly test this without invoking models

    def test_router_initialization_without_hooks(self):
        """Test router initialization without hooks"""
        router = ModelRouter(enable_routing=True, hooks=None)

        assert router.hooks is None


class TestQEFleetHooksIntegration:
    """Test suite for QEFleet with hooks"""

    def test_fleet_initialization_with_hooks(self):
        """Test fleet initialization with hooks enabled"""
        fleet = QEFleet(enable_hooks=True, fleet_id="test-fleet")

        assert fleet.enable_hooks is True
        assert fleet.hooks is not None
        assert fleet.hooks.fleet_id == "test-fleet"
        assert fleet.router.hooks is fleet.hooks

    def test_fleet_initialization_without_hooks(self):
        """Test fleet initialization with hooks disabled"""
        fleet = QEFleet(enable_hooks=False)

        assert fleet.enable_hooks is False
        assert fleet.hooks is None

    def test_fleet_get_metrics_with_hooks(self):
        """Test fleet metrics retrieval with hooks enabled"""
        fleet = QEFleet(enable_hooks=True, fleet_id="test")

        metrics = fleet.get_metrics()

        assert "fleet_id" in metrics
        assert "hooks" in metrics
        assert "configuration" in metrics
        assert metrics["configuration"]["hooks_enabled"] is True

    def test_fleet_get_metrics_without_hooks(self):
        """Test fleet metrics retrieval with hooks disabled"""
        fleet = QEFleet(enable_hooks=False)

        metrics = fleet.get_metrics()

        assert "hooks" in metrics
        assert metrics["hooks"]["enabled"] is False

    def test_fleet_get_call_count_with_hooks(self):
        """Test call count retrieval with hooks enabled"""
        fleet = QEFleet(enable_hooks=True)

        # Should not raise
        count = fleet.get_call_count()
        assert count == 0  # No calls yet

    def test_fleet_get_call_count_without_hooks(self):
        """Test call count retrieval with hooks disabled raises error"""
        fleet = QEFleet(enable_hooks=False)

        with pytest.raises(RuntimeError) as exc_info:
            fleet.get_call_count()

        assert "Hooks are not enabled" in str(exc_info.value)

    def test_fleet_get_cost_summary_with_hooks(self):
        """Test cost summary with hooks enabled"""
        fleet = QEFleet(enable_hooks=True)

        summary = fleet.get_cost_summary()

        assert isinstance(summary, str)
        assert "QE Fleet Metrics Summary" in summary

    def test_fleet_get_cost_summary_without_hooks(self):
        """Test cost summary with hooks disabled"""
        fleet = QEFleet(enable_hooks=False)

        summary = fleet.get_cost_summary()

        assert summary == "Hooks disabled - no cost tracking available"

    def test_fleet_get_dashboard_with_hooks(self):
        """Test dashboard with hooks enabled"""
        fleet = QEFleet(enable_hooks=True, fleet_id="test")

        dashboard = fleet.get_dashboard()

        assert isinstance(dashboard, str)
        assert "Dashboard" in dashboard

    def test_fleet_get_dashboard_without_hooks(self):
        """Test dashboard with hooks disabled"""
        fleet = QEFleet(enable_hooks=False)

        dashboard = fleet.get_dashboard()

        assert dashboard == "Hooks disabled - no dashboard available"

    def test_fleet_export_hooks_metrics(self):
        """Test exporting hook metrics"""
        fleet = QEFleet(enable_hooks=True)

        json_metrics = fleet.export_hooks_metrics(format="json")

        assert isinstance(json_metrics, str)
        assert "{" in json_metrics  # Valid JSON

    def test_fleet_reset_metrics_with_hooks(self):
        """Test metrics reset with hooks enabled"""
        fleet = QEFleet(enable_hooks=True)

        # Should not raise
        fleet.reset_metrics()

        # Verify reset
        assert fleet.get_call_count() == 0

    def test_fleet_reset_metrics_without_hooks(self):
        """Test metrics reset with hooks disabled (should not raise)"""
        fleet = QEFleet(enable_hooks=False)

        # Should log warning but not raise
        fleet.reset_metrics()

    def test_fleet_custom_cost_threshold(self):
        """Test fleet with custom cost alert threshold"""
        fleet = QEFleet(
            enable_hooks=True,
            cost_alert_threshold=25.0
        )

        assert fleet.hooks.cost_alert_threshold == 25.0


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow_with_hooks(self):
        """Test complete workflow with hooks tracking"""
        # Create fleet with hooks
        fleet = QEFleet(
            enable_hooks=True,
            enable_routing=True,
            fleet_id="integration-test"
        )

        # Verify hooks are properly integrated
        assert fleet.hooks is not None
        assert fleet.router.hooks is fleet.hooks

        # Get initial metrics
        initial_metrics = fleet.get_metrics()
        assert initial_metrics["hooks"]["total_calls"] == 0

        # Note: Actually invoking models requires API keys
        # In real integration tests, you would:
        # 1. Execute some agent tasks
        # 2. Verify call count increased
        # 3. Verify costs were tracked
        # 4. Verify metrics are accurate

    def test_metrics_persistence_across_operations(self):
        """Test that metrics persist across multiple operations"""
        fleet = QEFleet(enable_hooks=True)

        # Simulate multiple calls by directly manipulating hooks
        fleet.hooks.call_count = 5
        fleet.hooks.cost_tracker["total"] = 0.025

        # Get metrics
        metrics1 = fleet.get_metrics()
        assert metrics1["hooks"]["total_calls"] == 5

        # Add more calls
        fleet.hooks.call_count += 3
        fleet.hooks.cost_tracker["total"] += 0.015

        # Verify cumulative tracking
        metrics2 = fleet.get_metrics()
        assert metrics2["hooks"]["total_calls"] == 8
        assert metrics2["hooks"]["total_cost"] == 0.040

    def test_multi_agent_cost_tracking(self):
        """Test cost tracking across multiple agents"""
        fleet = QEFleet(enable_hooks=True)

        # Simulate costs from different agents
        fleet.hooks.cost_tracker["by_agent"]["agent1"] = {
            "total_cost": 0.10,
            "call_count": 10,
            "total_tokens": 10000
        }
        fleet.hooks.cost_tracker["by_agent"]["agent2"] = {
            "total_cost": 0.20,
            "call_count": 5,
            "total_tokens": 15000
        }
        fleet.hooks.cost_tracker["total"] = 0.30

        metrics = fleet.get_metrics()

        assert len(metrics["hooks"]["by_agent"]) == 2
        assert metrics["hooks"]["by_agent"]["agent1"]["total_cost"] == 0.10
        assert metrics["hooks"]["by_agent"]["agent2"]["total_cost"] == 0.20
