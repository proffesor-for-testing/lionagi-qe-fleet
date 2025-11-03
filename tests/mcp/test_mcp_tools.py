"""Tests for MCP tool implementations"""

import pytest
from lionagi_qe.mcp import mcp_tools
from lionagi_qe.mcp.mcp_server import create_mcp_server


@pytest.fixture
async def initialized_fleet():
    """Fixture that provides an initialized fleet"""
    server = create_mcp_server()
    await server.start()

    yield server.fleet

    await server.stop()


@pytest.mark.asyncio
class TestCoreTools:
    """Test core testing tools"""

    async def test_test_generate_enum_types(self):
        """Test enum types for test_generate"""
        # Test that enum types are defined
        assert hasattr(mcp_tools, "TestFramework")
        assert hasattr(mcp_tools, "TestType")

        # Test enum values
        assert mcp_tools.TestFramework.PYTEST == "pytest"
        assert mcp_tools.TestFramework.JEST == "jest"
        assert mcp_tools.TestType.UNIT == "unit"
        assert mcp_tools.TestType.INTEGRATION == "integration"

    async def test_scan_type_enum(self):
        """Test security scan type enum"""
        assert hasattr(mcp_tools, "ScanType")
        assert mcp_tools.ScanType.SAST == "sast"
        assert mcp_tools.ScanType.DAST == "dast"
        assert mcp_tools.ScanType.COMPREHENSIVE == "comprehensive"


@pytest.mark.asyncio
class TestToolExecution:
    """Test actual tool execution with initialized fleet"""

    async def test_get_fleet_status(self, initialized_fleet):
        """Test get_fleet_status returns expected structure"""
        status = await mcp_tools.get_fleet_status()

        assert isinstance(status, dict)
        assert "initialized" in status or "status" in status

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_test_generate_execution(self, initialized_fleet):
        """Test test_generate tool execution"""
        result = await mcp_tools.test_generate(
            code="def add(a, b): return a + b",
            framework=mcp_tools.TestFramework.PYTEST,
            test_type=mcp_tools.TestType.UNIT,
            coverage_target=80.0
        )

        assert isinstance(result, dict)
        assert "test_code" in result
        assert "test_name" in result
        assert "framework" in result

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_test_execute_execution(self, initialized_fleet):
        """Test test_execute tool execution"""
        result = await mcp_tools.test_execute(
            test_path="./tests",
            framework=mcp_tools.TestFramework.PYTEST,
            parallel=True,
            coverage=True
        )

        assert isinstance(result, dict)
        assert "passed" in result
        assert "failed" in result
        assert "coverage" in result

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_coverage_analyze_execution(self, initialized_fleet):
        """Test coverage_analyze tool execution"""
        result = await mcp_tools.coverage_analyze(
            source_path="./src",
            test_path="./tests",
            threshold=80.0
        )

        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_quality_gate_execution(self, initialized_fleet):
        """Test quality_gate tool execution"""
        result = await mcp_tools.quality_gate(
            metrics={
                "coverage": 85.0,
                "complexity": 7.5
            }
        )

        assert isinstance(result, dict)
        assert "passed" in result
        assert "score" in result


@pytest.mark.asyncio
class TestFleetOrchestration:
    """Test fleet orchestration tools"""

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_fleet_orchestrate_pipeline(self, initialized_fleet):
        """Test pipeline orchestration"""
        result = await mcp_tools.fleet_orchestrate(
            workflow="pipeline",
            context={},
            agents=["test-generator", "test-executor"]
        )

        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_fleet_orchestrate_parallel(self, initialized_fleet):
        """Test parallel orchestration"""
        result = await mcp_tools.fleet_orchestrate(
            workflow="parallel",
            context={"tasks": []},
            agents=["test-generator", "security-scanner"]
        )

        assert isinstance(result, dict)

    async def test_fleet_orchestrate_invalid_workflow(self, initialized_fleet):
        """Test invalid workflow type raises error"""
        with pytest.raises(ValueError, match="Unknown workflow type"):
            await mcp_tools.fleet_orchestrate(
                workflow="invalid",
                context={},
                agents=[]
            )


@pytest.mark.asyncio
class TestStreamingTools:
    """Test streaming tool implementations"""

    @pytest.mark.skip(reason="Requires full agent implementation")
    async def test_test_execute_stream(self, initialized_fleet):
        """Test streaming test execution"""
        events = []

        async for event in mcp_tools.test_execute_stream(
            test_path="./tests",
            framework=mcp_tools.TestFramework.PYTEST
        ):
            events.append(event)

            if event["type"] == "progress":
                assert "percent" in event
                assert "message" in event
            elif event["type"] == "result":
                assert "data" in event

        # Should have progress events and final result
        assert len(events) > 0
        assert events[-1]["type"] == "result"


@pytest.mark.asyncio
class TestAdvancedTools:
    """Test advanced tool signatures"""

    async def test_requirements_validate_signature(self):
        """Test requirements_validate has correct signature"""
        import inspect

        sig = inspect.signature(mcp_tools.requirements_validate)
        params = sig.parameters

        assert "requirements" in params
        assert "format" in params

    async def test_flaky_test_hunt_signature(self):
        """Test flaky_test_hunt has correct signature"""
        import inspect

        sig = inspect.signature(mcp_tools.flaky_test_hunt)
        params = sig.parameters

        assert "test_path" in params
        assert "iterations" in params
        assert "detect_threshold" in params

    async def test_api_contract_validate_signature(self):
        """Test api_contract_validate has correct signature"""
        import inspect

        sig = inspect.signature(mcp_tools.api_contract_validate)
        params = sig.parameters

        assert "spec_path" in params
        assert "version_a" in params
        assert "version_b" in params

    async def test_regression_risk_analyze_signature(self):
        """Test regression_risk_analyze has correct signature"""
        import inspect

        sig = inspect.signature(mcp_tools.regression_risk_analyze)
        params = sig.parameters

        assert "changes" in params
        assert "test_suite" in params
        assert "ml_enabled" in params
