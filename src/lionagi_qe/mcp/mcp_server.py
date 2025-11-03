"""MCP Server implementation for LionAGI QE Fleet

FastMCP-based server that exposes all QE agents as MCP tools
for seamless integration with Claude Code and other MCP clients.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Fallback implementation for when FastMCP is not available
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
            self._tools = {}

        def tool(self, func):
            self._tools[func.__name__] = func
            return func

from lionagi_qe.core.fleet import QEFleet
from lionagi_qe.agents import TestGeneratorAgent, TestExecutorAgent, FleetCommanderAgent
from lionagi import iModel

from . import mcp_tools


logger = logging.getLogger("lionagi_qe.mcp")


class MCPServer:
    """MCP Server for LionAGI QE Fleet

    Exposes all 19 QE agents as MCP tools for Claude Code integration.
    Supports tool discovery, execution, and streaming results.
    """

    def __init__(
        self,
        name: str = "lionagi-qe",
        enable_routing: bool = True,
        enable_learning: bool = False,
    ):
        """Initialize MCP server

        Args:
            name: Server name for MCP registration
            enable_routing: Enable multi-model routing
            enable_learning: Enable Q-learning
        """
        self.name = name
        self.enable_routing = enable_routing
        self.enable_learning = enable_learning

        # Initialize FastMCP server
        self.mcp = FastMCP(name)

        # QE Fleet instance
        self.fleet: Optional[QEFleet] = None

        # Setup logging
        self.logger = logging.getLogger(f"lionagi_qe.mcp.{name}")

        # Register all tools
        self._register_tools()

    async def initialize_fleet(self):
        """Initialize the QE Fleet and register agents"""
        if self.fleet is not None:
            self.logger.warning("Fleet already initialized")
            return

        self.logger.info("Initializing LionAGI QE Fleet for MCP...")

        # Create fleet
        self.fleet = QEFleet(
            enable_routing=self.enable_routing,
            enable_learning=self.enable_learning
        )

        await self.fleet.initialize()

        # Initialize a default model (can be overridden by routing)
        model = iModel(provider="openai", model="gpt-4")

        # Register core agents
        test_gen = TestGeneratorAgent(
            agent_id="test-generator",
            model=model,
            memory=self.fleet.memory,
            skills=["agentic-quality-engineering", "tdd-london-chicago", "api-testing-patterns"],
            enable_learning=self.enable_learning
        )
        self.fleet.register_agent(test_gen)

        test_exec = TestExecutorAgent(
            agent_id="test-executor",
            model=model,
            memory=self.fleet.memory,
            skills=["agentic-quality-engineering", "shift-left-testing"],
            enable_learning=self.enable_learning
        )
        self.fleet.register_agent(test_exec)

        commander = FleetCommanderAgent(
            agent_id="fleet-commander",
            model=model,
            memory=self.fleet.memory,
            skills=["agentic-quality-engineering", "holistic-testing-pact"],
            enable_learning=self.enable_learning
        )
        self.fleet.register_agent(commander)

        # Set fleet instance for tools
        mcp_tools.set_fleet_instance(self.fleet)

        self.logger.info("✓ QE Fleet initialized for MCP")

    def _register_tools(self):
        """Register all MCP tools"""

        # Core Testing Tools
        self.mcp.tool()(mcp_tools.test_generate)
        self.mcp.tool()(mcp_tools.test_execute)
        self.mcp.tool()(mcp_tools.coverage_analyze)
        self.mcp.tool()(mcp_tools.quality_gate)

        # Performance & Security
        self.mcp.tool()(mcp_tools.performance_test)
        self.mcp.tool()(mcp_tools.security_scan)

        # Fleet Orchestration
        self.mcp.tool()(mcp_tools.fleet_orchestrate)
        self.mcp.tool()(mcp_tools.get_fleet_status)

        # Advanced Tools
        self.mcp.tool()(mcp_tools.requirements_validate)
        self.mcp.tool()(mcp_tools.flaky_test_hunt)
        self.mcp.tool()(mcp_tools.api_contract_validate)
        self.mcp.tool()(mcp_tools.regression_risk_analyze)
        self.mcp.tool()(mcp_tools.test_data_generate)
        self.mcp.tool()(mcp_tools.visual_test)
        self.mcp.tool()(mcp_tools.chaos_test)
        self.mcp.tool()(mcp_tools.deployment_readiness)

        # Streaming tools
        self.mcp.tool()(mcp_tools.test_execute_stream)

        self.logger.info(f"Registered {len(self.mcp._tools)} MCP tools")

    async def start(self):
        """Start the MCP server"""
        await self.initialize_fleet()
        self.logger.info(f"MCP Server '{self.name}' ready")

    async def stop(self):
        """Stop the MCP server and cleanup"""
        if self.fleet:
            # Export state before shutdown
            state = await self.fleet.export_state()
            self.logger.info("Fleet state exported")

        self.logger.info(f"MCP Server '{self.name}' stopped")

    def get_server(self) -> FastMCP:
        """Get the FastMCP server instance

        Returns:
            FastMCP server instance
        """
        return self.mcp


# ============================================================================
# Server Factory & Entrypoint
# ============================================================================

def create_mcp_server(
    name: str = "lionagi-qe",
    enable_routing: bool = True,
    enable_learning: bool = False,
) -> MCPServer:
    """Create and configure an MCP server instance

    Args:
        name: Server name
        enable_routing: Enable multi-model routing
        enable_learning: Enable Q-learning

    Returns:
        Configured MCPServer instance
    """
    return MCPServer(
        name=name,
        enable_routing=enable_routing,
        enable_learning=enable_learning,
    )


async def run_mcp_server():
    """Main entrypoint for running the MCP server"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and start server
    server = create_mcp_server()

    try:
        await server.start()

        # Run the MCP server
        if MCP_AVAILABLE:
            # Use FastMCP's run method
            await server.get_server().run()
        else:
            logger.warning("FastMCP not available, running in fallback mode")
            # Keep server running
            while True:
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    finally:
        await server.stop()


# ============================================================================
# Standalone Server Runner
# ============================================================================

if __name__ == "__main__":
    """
    Run the MCP server standalone:

    python -m lionagi_qe.mcp.mcp_server
    """
    asyncio.run(run_mcp_server())
