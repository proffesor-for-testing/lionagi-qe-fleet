"""MCP (Model Context Protocol) integration for LionAGI QE Fleet

This module provides MCP server implementation for Claude Code compatibility,
exposing all QE agents as MCP tools for seamless integration.
"""

from .mcp_server import MCPServer
from .mcp_tools import (
    test_generate,
    test_execute,
    coverage_analyze,
    quality_gate,
    fleet_orchestrate,
    performance_test,
    security_scan,
    get_fleet_status,
)

__all__ = [
    "MCPServer",
    "test_generate",
    "test_execute",
    "coverage_analyze",
    "quality_gate",
    "fleet_orchestrate",
    "performance_test",
    "security_scan",
    "get_fleet_status",
]
