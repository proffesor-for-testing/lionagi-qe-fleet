"""
Base CLI classes and exit code definitions.

Provides standardized exit codes and base command structure
for all CLI commands.
"""

from enum import IntEnum
from typing import Any, Dict, Optional
from dataclasses import dataclass


class ExitCode(IntEnum):
    """Standardized exit codes for CLI commands."""

    SUCCESS = 0          # Operation completed successfully
    ERROR = 1            # Operation failed with error
    WARNING = 2          # Operation completed with warnings (soft failure)

    # Specific error codes
    INVALID_INPUT = 3    # Invalid input parameters
    TIMEOUT = 4          # Operation timed out
    PERMISSION = 5       # Permission denied
    NOT_FOUND = 6        # Resource not found
    CONFLICT = 7         # Resource conflict


@dataclass
class CLIOutput:
    """
    Structured output for CLI commands.

    Attributes:
        success: Whether the operation succeeded
        data: Operation result data
        message: Human-readable message
        warnings: List of warning messages
        errors: List of error messages
        exit_code: Exit code for the operation
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    warnings: list[str] = None
    errors: list[str] = None
    exit_code: ExitCode = ExitCode.SUCCESS

    def __post_init__(self):
        """Initialize empty lists for warnings and errors."""
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

        # Auto-determine exit code if not set
        if self.exit_code == ExitCode.SUCCESS:
            if self.errors:
                self.exit_code = ExitCode.ERROR
            elif self.warnings:
                self.exit_code = ExitCode.WARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convert output to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "data": self.data or {},
            "message": self.message,
            "warnings": self.warnings,
            "errors": self.errors,
            "exitCode": int(self.exit_code)
        }


class BaseCLICommand:
    """
    Base class for all CLI commands with CI/CD support.

    Provides common functionality for:
    - JSON output formatting
    - Quiet mode
    - Non-interactive mode
    - Standardized exit codes
    """

    def __init__(
        self,
        json_output: bool = False,
        quiet: bool = False,
        non_interactive: bool = False,
        ci_mode: bool = False
    ):
        """
        Initialize CLI command.

        Args:
            json_output: Output in JSON format
            quiet: Minimal output (errors only)
            non_interactive: No user prompts
            ci_mode: CI mode (combines json + quiet + non_interactive)
        """
        # CI mode enables all flags
        if ci_mode:
            json_output = True
            quiet = True
            non_interactive = True

        self.json_output = json_output
        self.quiet = quiet
        self.non_interactive = non_interactive
        self.ci_mode = ci_mode

    def should_print(self, level: str = "info") -> bool:
        """
        Determine if message should be printed based on quiet mode.

        Args:
            level: Message level (info, warning, error)

        Returns:
            True if message should be printed
        """
        if self.quiet:
            return level in ("error", "warning")
        return True

    def prompt_user(self, message: str, default: Optional[str] = None) -> str:
        """
        Prompt user for input (fails in non-interactive mode).

        Args:
            message: Prompt message
            default: Default value if non-interactive

        Returns:
            User input or default value

        Raises:
            RuntimeError: If non-interactive and no default provided
        """
        if self.non_interactive:
            if default is None:
                raise RuntimeError(
                    f"Cannot prompt in non-interactive mode: {message}"
                )
            return default

        try:
            return input(f"{message}: ")
        except (EOFError, KeyboardInterrupt):
            if default is not None:
                return default
            raise

    def validate_required_input(self, name: str, value: Optional[Any]) -> Any:
        """
        Validate required input (fails fast in non-interactive mode).

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            Validated value

        Raises:
            ValueError: If value is None/empty in non-interactive mode
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if self.non_interactive:
                raise ValueError(
                    f"Required parameter '{name}' is missing. "
                    f"Cannot prompt in non-interactive mode."
                )
        return value
