"""
Output formatting for CLI commands.

Handles JSON and human-readable output formatting.
"""

import json
import sys
from typing import Any, Dict, Optional
from .base import CLIOutput, ExitCode


class OutputFormatter:
    """
    Formatter for CLI output supporting multiple formats.

    Supports:
    - JSON output for CI/CD systems
    - Human-readable text output
    - Color support (when not in CI mode)
    """

    def __init__(
        self,
        json_format: bool = False,
        quiet: bool = False,
        color: bool = True
    ):
        """
        Initialize output formatter.

        Args:
            json_format: Output in JSON format
            quiet: Minimal output mode
            color: Enable color output (auto-disabled in JSON mode)
        """
        self.json_format = json_format
        self.quiet = quiet
        self.color = color and not json_format

        # ANSI color codes
        self.COLORS = {
            "reset": "\033[0m" if self.color else "",
            "red": "\033[91m" if self.color else "",
            "green": "\033[92m" if self.color else "",
            "yellow": "\033[93m" if self.color else "",
            "blue": "\033[94m" if self.color else "",
            "gray": "\033[90m" if self.color else "",
        }

    def format_output(self, output: CLIOutput) -> str:
        """
        Format CLI output based on configuration.

        Args:
            output: CLI output to format

        Returns:
            Formatted output string
        """
        if self.json_format:
            return self._format_json(output)
        else:
            return self._format_text(output)

    def _format_json(self, output: CLIOutput) -> str:
        """Format output as JSON."""
        return json.dumps(output.to_dict(), indent=2)

    def _format_text(self, output: CLIOutput) -> str:
        """Format output as human-readable text."""
        lines = []

        # Status indicator
        if output.success:
            status = f"{self.COLORS['green']}✓ SUCCESS{self.COLORS['reset']}"
        else:
            status = f"{self.COLORS['red']}✗ FAILED{self.COLORS['reset']}"

        if not self.quiet:
            lines.append(status)

        # Message
        if output.message and not self.quiet:
            lines.append(f"\n{output.message}")

        # Warnings
        if output.warnings:
            if not self.quiet:
                lines.append(f"\n{self.COLORS['yellow']}Warnings:{self.COLORS['reset']}")
            for warning in output.warnings:
                lines.append(f"  {self.COLORS['yellow']}⚠{self.COLORS['reset']} {warning}")

        # Errors
        if output.errors:
            lines.append(f"\n{self.COLORS['red']}Errors:{self.COLORS['reset']}")
            for error in output.errors:
                lines.append(f"  {self.COLORS['red']}✗{self.COLORS['reset']} {error}")

        # Data (in quiet mode, only show essential data)
        if output.data and not self.quiet:
            lines.append(f"\n{self._format_data(output.data)}")

        return "\n".join(lines)

    def _format_data(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Format data dictionary as readable text."""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{self.COLORS['blue']}{key}:{self.COLORS['reset']}")
                lines.append(self._format_data(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{self.COLORS['blue']}{key}:{self.COLORS['reset']}")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._format_data(item, indent + 1))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{self.COLORS['blue']}{key}:{self.COLORS['reset']} {value}")

        return "\n".join(lines)

    def print_output(self, output: CLIOutput) -> None:
        """
        Print formatted output and exit with appropriate code.

        Args:
            output: CLI output to print
        """
        formatted = self.format_output(output)
        if formatted:
            print(formatted)
        sys.exit(output.exit_code)

    def print_error(self, message: str, exit_code: ExitCode = ExitCode.ERROR) -> None:
        """
        Print error message and exit.

        Args:
            message: Error message
            exit_code: Exit code to use
        """
        output = CLIOutput(
            success=False,
            message="",
            errors=[message],
            exit_code=exit_code
        )
        self.print_output(output)

    def print_success(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        warnings: Optional[list[str]] = None
    ) -> None:
        """
        Print success message and exit.

        Args:
            message: Success message
            data: Optional data to include
            warnings: Optional warnings
        """
        exit_code = ExitCode.WARNING if warnings else ExitCode.SUCCESS
        output = CLIOutput(
            success=True,
            message=message,
            data=data,
            warnings=warnings or [],
            exit_code=exit_code
        )
        self.print_output(output)

    def print_progress(self, message: str) -> None:
        """
        Print progress message (suppressed in quiet mode).

        Args:
            message: Progress message
        """
        if not self.quiet and not self.json_format:
            print(f"{self.COLORS['gray']}→{self.COLORS['reset']} {message}")
