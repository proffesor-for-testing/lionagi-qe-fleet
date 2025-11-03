"""Tests for MCP Server implementation"""

import pytest
import asyncio
from lionagi_qe.mcp.mcp_server import MCPServer, create_mcp_server


class TestMCPServer:
    """Test MCP Server initialization and configuration"""

    def test_create_mcp_server(self):
        """Test server creation with default config"""
        server = create_mcp_server()

        assert server.name == "lionagi-qe"
        assert server.enable_routing is True
        assert server.enable_learning is False
        assert server.fleet is None  # Not initialized yet

    def test_create_mcp_server_custom_config(self):
        """Test server creation with custom config"""
        server = create_mcp_server(
            name="custom-qe",
            enable_routing=False,
            enable_learning=True
        )

        assert server.name == "custom-qe"
        assert server.enable_routing is False
        assert server.enable_learning is True

    @pytest.mark.asyncio
    async def test_initialize_fleet(self):
        """Test fleet initialization"""
        server = create_mcp_server()

        await server.initialize_fleet()

        assert server.fleet is not None
        assert server.fleet.initialized is True

        # Verify core agents are registered
        test_gen = await server.fleet.get_agent("test-generator")
        test_exec = await server.fleet.get_agent("test-executor")
        commander = await server.fleet.get_agent("fleet-commander")

        assert test_gen is not None
        assert test_exec is not None
        assert commander is not None

        await server.stop()

    @pytest.mark.asyncio
    async def test_double_initialization(self):
        """Test that double initialization is safe"""
        server = create_mcp_server()

        await server.initialize_fleet()
        fleet1 = server.fleet

        await server.initialize_fleet()
        fleet2 = server.fleet

        # Should be the same instance
        assert fleet1 is fleet2

        await server.stop()

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test server start and stop lifecycle"""
        server = create_mcp_server()

        await server.start()
        assert server.fleet is not None
        assert server.fleet.initialized is True

        await server.stop()
        # Server should be cleanly stopped

    def test_get_server(self):
        """Test getting FastMCP server instance"""
        server = create_mcp_server()
        mcp = server.get_server()

        assert mcp is not None
        assert mcp.name == "lionagi-qe"
        assert len(mcp._tools) > 0  # Tools should be registered


class TestMCPTools:
    """Test MCP tool registration"""

    def test_tools_registered(self):
        """Test that all tools are registered"""
        server = create_mcp_server()
        mcp = server.get_server()

        # Core tools
        assert "test_generate" in mcp._tools
        assert "test_execute" in mcp._tools
        assert "coverage_analyze" in mcp._tools
        assert "quality_gate" in mcp._tools

        # Performance & Security
        assert "performance_test" in mcp._tools
        assert "security_scan" in mcp._tools

        # Fleet Orchestration
        assert "fleet_orchestrate" in mcp._tools
        assert "get_fleet_status" in mcp._tools

        # Advanced tools
        assert "requirements_validate" in mcp._tools
        assert "flaky_test_hunt" in mcp._tools
        assert "api_contract_validate" in mcp._tools
        assert "regression_risk_analyze" in mcp._tools
        assert "test_data_generate" in mcp._tools
        assert "visual_test" in mcp._tools
        assert "chaos_test" in mcp._tools
        assert "deployment_readiness" in mcp._tools

        # Streaming
        assert "test_execute_stream" in mcp._tools

    def test_tool_count(self):
        """Test that expected number of tools are registered"""
        server = create_mcp_server()
        mcp = server.get_server()

        # Should have 17 tools
        assert len(mcp._tools) >= 17


@pytest.mark.asyncio
class TestMCPIntegration:
    """Integration tests for MCP server"""

    async def test_fleet_status_tool(self):
        """Test get_fleet_status tool"""
        from lionagi_qe.mcp import mcp_tools

        server = create_mcp_server()
        await server.start()

        # Get fleet status
        status = await mcp_tools.get_fleet_status()

        assert status is not None
        assert "initialized" in status

        await server.stop()

    async def test_tool_requires_initialized_fleet(self):
        """Test that tools require initialized fleet"""
        from lionagi_qe.mcp import mcp_tools

        # Reset fleet instance
        mcp_tools.set_fleet_instance(None)

        # Should raise error
        with pytest.raises(RuntimeError, match="Fleet not initialized"):
            await mcp_tools.get_fleet_status()
