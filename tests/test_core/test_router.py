"""Unit tests for ModelRouter - Multi-model routing for cost optimization"""

import pytest
from lionagi_qe.core.router import ModelRouter, TaskComplexity
from unittest.mock import AsyncMock, MagicMock, patch


class TestTaskComplexity:
    """Test TaskComplexity model"""

    def test_task_complexity_creation(self):
        """Test creating TaskComplexity instance"""
        complexity = TaskComplexity(
            level="simple",
            reasoning="Basic unit test generation",
            estimated_tokens=100,
            confidence=0.9
        )

        assert complexity.level == "simple"
        assert complexity.reasoning == "Basic unit test generation"
        assert complexity.estimated_tokens == 100
        assert complexity.confidence == 0.9

    def test_task_complexity_validation(self):
        """Test TaskComplexity field validation"""
        # Valid levels
        for level in ["simple", "moderate", "complex", "critical"]:
            complexity = TaskComplexity(
                level=level,
                reasoning="test"
            )
            assert complexity.level == level

    def test_task_complexity_defaults(self):
        """Test TaskComplexity default values"""
        complexity = TaskComplexity(
            level="simple",
            reasoning="test"
        )

        assert complexity.estimated_tokens == 0
        assert complexity.confidence == 0.8


class TestModelRouter:
    """Test ModelRouter initialization and configuration"""

    def test_init_with_routing_enabled(self):
        """Test router initialization with routing enabled"""
        router = ModelRouter(enable_routing=True)

        assert router.enable_routing is True
        assert "simple" in router.models
        assert "moderate" in router.models
        assert "complex" in router.models
        assert "critical" in router.models

    def test_init_with_routing_disabled(self):
        """Test router initialization with routing disabled"""
        router = ModelRouter(enable_routing=False)

        assert router.enable_routing is False
        assert len(router.models) == 4

    def test_cost_configuration(self):
        """Test cost per model is configured"""
        router = ModelRouter()

        assert router.costs["simple"] == 0.0004
        assert router.costs["moderate"] == 0.0008
        assert router.costs["complex"] == 0.0048
        assert router.costs["critical"] == 0.0065

    def test_stats_initialization(self):
        """Test routing statistics initialization"""
        router = ModelRouter()

        assert router.stats["total_requests"] == 0
        assert router.stats["by_complexity"]["simple"] == 0
        assert router.stats["total_cost"] == 0.0
        assert router.stats["estimated_savings"] == 0.0

    def test_model_pool_configuration(self):
        """Test model pool is properly configured"""
        router = ModelRouter()

        # Check all models are iModel instances
        for model in router.models.values():
            assert hasattr(model, 'provider')

    @pytest.mark.asyncio
    async def test_analyze_complexity_simple(self, model_router, mocker):
        """Test complexity analysis for simple tasks"""
        # Mock the analyzer response
        mock_result = TaskComplexity(
            level="simple",
            reasoning="Basic unit test generation with simple assertions",
            estimated_tokens=150,
            confidence=0.95
        )

        mock_operate = mocker.patch.object(
            model_router._analyzer,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        result = await model_router.analyze_complexity(
            task_type="unit_test_generation",
            context={"code": "def add(a, b): return a + b"}
        )

        assert result.level == "simple"
        assert "simple" in result.reasoning.lower() or "basic" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_analyze_complexity_complex(self, model_router, mocker):
        """Test complexity analysis for complex tasks"""
        mock_result = TaskComplexity(
            level="complex",
            reasoning="Property-based testing with edge case generation",
            estimated_tokens=800,
            confidence=0.85
        )

        mocker.patch.object(
            model_router._analyzer,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        result = await model_router.analyze_complexity(
            task_type="property_based_testing",
            context={"complexity": "high", "edge_cases": True}
        )

        assert result.level == "complex"

    @pytest.mark.asyncio
    async def test_route_with_routing_disabled(self, model_router):
        """Test routing when disabled returns moderate model"""
        model, cost, complexity = await model_router.route(
            task_type="test_generation",
            context={}
        )

        assert model == model_router.models["moderate"]
        assert cost == model_router.costs["moderate"]
        assert complexity.level == "moderate"
        assert "disabled" in complexity.reasoning.lower()

    @pytest.mark.asyncio
    async def test_route_simple_task(self, mocker):
        """Test routing simple task to GPT-3.5"""
        router = ModelRouter(enable_routing=True)

        # Mock complexity analysis
        mock_complexity = TaskComplexity(
            level="simple",
            reasoning="Basic validation",
            confidence=0.9
        )

        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=mock_complexity)
        )

        model, cost, complexity = await router.route(
            task_type="unit_test",
            context={"code": "simple"}
        )

        assert model == router.models["simple"]
        assert cost == router.costs["simple"]
        assert complexity.level == "simple"

    @pytest.mark.asyncio
    async def test_route_critical_task(self, mocker):
        """Test routing critical task to Claude Sonnet"""
        router = ModelRouter(enable_routing=True)

        mock_complexity = TaskComplexity(
            level="critical",
            reasoning="Security audit and architecture review",
            confidence=0.95
        )

        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=mock_complexity)
        )

        model, cost, complexity = await router.route(
            task_type="security_audit",
            context={"scope": "production"}
        )

        assert model == router.models["critical"]
        assert cost == router.costs["critical"]

    @pytest.mark.asyncio
    async def test_route_updates_stats(self, mocker):
        """Test routing updates statistics"""
        router = ModelRouter(enable_routing=True)

        mock_complexity = TaskComplexity(
            level="simple",
            reasoning="Test",
            confidence=0.9
        )

        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=mock_complexity)
        )

        initial_requests = router.stats["total_requests"]
        initial_simple = router.stats["by_complexity"]["simple"]

        await router.route("test_task", {})

        assert router.stats["total_requests"] == initial_requests + 1
        assert router.stats["by_complexity"]["simple"] == initial_simple + 1
        assert router.stats["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_route_calculates_savings(self, mocker):
        """Test routing calculates cost savings"""
        router = ModelRouter(enable_routing=True)

        mock_complexity = TaskComplexity(
            level="simple",
            reasoning="Test",
            confidence=0.9
        )

        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=mock_complexity)
        )

        await router.route("test_task", {})

        # Simple model is cheaper than complex baseline
        assert router.stats["estimated_savings"] > 0

    def test_get_model_by_level(self):
        """Test getting model by complexity level"""
        router = ModelRouter()

        assert router.get_model("simple") == router.models["simple"]
        assert router.get_model("moderate") == router.models["moderate"]
        assert router.get_model("complex") == router.models["complex"]
        assert router.get_model("critical") == router.models["critical"]

    def test_get_model_invalid_level(self):
        """Test getting model with invalid level returns moderate"""
        router = ModelRouter()

        assert router.get_model("invalid") == router.models["moderate"]
        assert router.get_model("") == router.models["moderate"]

    @pytest.mark.asyncio
    async def test_get_routing_stats_empty(self):
        """Test getting stats with no routing"""
        router = ModelRouter()

        stats = await router.get_routing_stats()

        assert stats["total_requests"] == 0
        assert stats["total_cost"] == 0.0
        assert "by_complexity" in stats

    @pytest.mark.asyncio
    async def test_get_routing_stats_with_data(self, mocker):
        """Test getting stats after routing"""
        router = ModelRouter(enable_routing=True)

        # Mock complexity analysis
        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=TaskComplexity(
                level="simple",
                reasoning="Test",
                confidence=0.9
            ))
        )

        # Route some tasks
        await router.route("task1", {})
        await router.route("task2", {})

        stats = await router.get_routing_stats()

        assert stats["total_requests"] == 2
        assert stats["average_cost"] > 0
        assert stats["savings_percentage"] > 0
        assert "distribution" in stats

    @pytest.mark.asyncio
    async def test_routing_distribution(self, mocker):
        """Test routing distribution across complexity levels"""
        router = ModelRouter(enable_routing=True)

        # Mock different complexity levels
        complexities = [
            TaskComplexity(level="simple", reasoning="Test", confidence=0.9),
            TaskComplexity(level="moderate", reasoning="Test", confidence=0.9),
            TaskComplexity(level="complex", reasoning="Test", confidence=0.9),
            TaskComplexity(level="simple", reasoning="Test", confidence=0.9),
        ]

        analyze_mock = mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock()
        )
        analyze_mock.side_effect = complexities

        # Route tasks
        for i in range(4):
            await router.route(f"task{i}", {})

        stats = await router.get_routing_stats()

        assert stats["by_complexity"]["simple"] == 2
        assert stats["by_complexity"]["moderate"] == 1
        assert stats["by_complexity"]["complex"] == 1
        assert stats["distribution"]["simple"] == 50.0

    @pytest.mark.asyncio
    async def test_cost_savings_calculation(self, mocker):
        """Test cost savings percentage calculation"""
        router = ModelRouter(enable_routing=True)

        # Route 10 simple tasks
        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=TaskComplexity(
                level="simple",
                reasoning="Test",
                confidence=0.9
            ))
        )

        for i in range(10):
            await router.route(f"task{i}", {})

        stats = await router.get_routing_stats()

        # Simple model is much cheaper than complex baseline
        # Should see significant savings
        assert stats["savings_percentage"] > 50
        assert stats["total_cost"] < 0.01  # 10 * 0.0004

    @pytest.mark.asyncio
    async def test_concurrent_routing(self, mocker):
        """Test concurrent routing requests"""
        import asyncio

        router = ModelRouter(enable_routing=True)

        mocker.patch.object(
            router,
            'analyze_complexity',
            new=AsyncMock(return_value=TaskComplexity(
                level="simple",
                reasoning="Test",
                confidence=0.9
            ))
        )

        # Route tasks concurrently
        tasks = [
            router.route(f"task{i}", {})
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert router.stats["total_requests"] == 5
