"""
Example CLI command implementations with CI/CD support.

Demonstrates how to use the CLI enhancement framework.
"""

from typing import Optional
from .base import BaseCLICommand, CLIOutput, ExitCode
from .output import OutputFormatter
from .ci_mode import CIModeConfig


class TestGenerateCommand(BaseCLICommand):
    """
    Example: Test generation command with CI/CD support.

    Usage:
        # Standard mode
        aqe generate src/

        # CI mode
        aqe generate src/ --ci-mode

        # Custom flags
        aqe generate src/ --json --quiet --non-interactive
    """

    def __init__(
        self,
        target_path: str,
        framework: str = "pytest",
        **cli_options
    ):
        """
        Initialize test generation command.

        Args:
            target_path: Path to generate tests for
            framework: Testing framework (pytest, jest, etc.)
            **cli_options: CLI flags (json_output, quiet, etc.)
        """
        super().__init__(**cli_options)
        self.target_path = target_path
        self.framework = framework
        self.formatter = OutputFormatter(
            json_format=self.json_output,
            quiet=self.quiet
        )

    def execute(self) -> CLIOutput:
        """
        Execute test generation.

        Returns:
            CLIOutput with results
        """
        try:
            # Validate inputs
            self.validate_required_input("target_path", self.target_path)

            # Print progress (suppressed in quiet mode)
            if not self.quiet:
                self.formatter.print_progress(
                    f"Generating tests for {self.target_path}..."
                )

            # Simulate test generation
            results = {
                "testsGenerated": 42,
                "coverage": 85.5,
                "framework": self.framework,
                "targetPath": self.target_path,
                "files": [
                    f"tests/test_{self.target_path.replace('/', '_')}.py"
                ]
            }

            warnings = []
            if results["coverage"] < 90:
                warnings.append(
                    f"Coverage {results['coverage']}% is below target 90%"
                )

            return CLIOutput(
                success=True,
                message=f"Generated {results['testsGenerated']} tests",
                data=results,
                warnings=warnings,
                exit_code=ExitCode.WARNING if warnings else ExitCode.SUCCESS
            )

        except ValueError as e:
            return CLIOutput(
                success=False,
                message="Test generation failed",
                errors=[str(e)],
                exit_code=ExitCode.INVALID_INPUT
            )
        except Exception as e:
            return CLIOutput(
                success=False,
                message="Test generation failed",
                errors=[str(e)],
                exit_code=ExitCode.ERROR
            )

    def run(self) -> None:
        """Execute command and print output."""
        output = self.execute()
        self.formatter.print_output(output)


class QualityGateCommand(BaseCLICommand):
    """
    Example: Quality gate validation with CI/CD support.

    Usage:
        # Check quality gate
        aqe quality-gate --threshold 80

        # CI mode (fails build if threshold not met)
        aqe quality-gate --threshold 80 --ci-mode
    """

    def __init__(
        self,
        threshold: float = 80.0,
        **cli_options
    ):
        """
        Initialize quality gate command.

        Args:
            threshold: Minimum quality threshold
            **cli_options: CLI flags
        """
        super().__init__(**cli_options)
        self.threshold = threshold
        self.formatter = OutputFormatter(
            json_format=self.json_output,
            quiet=self.quiet
        )

    def execute(self) -> CLIOutput:
        """
        Execute quality gate check.

        Returns:
            CLIOutput with results
        """
        try:
            # Simulate quality check
            current_quality = 85.5
            passed = current_quality >= self.threshold

            results = {
                "passed": passed,
                "currentQuality": current_quality,
                "threshold": self.threshold,
                "checks": {
                    "coverage": {"score": 85.5, "passed": True},
                    "complexity": {"score": 7.2, "passed": True},
                    "duplication": {"score": 3.1, "passed": True},
                    "security": {"score": 95.0, "passed": True}
                }
            }

            if passed:
                return CLIOutput(
                    success=True,
                    message=f"Quality gate passed ({current_quality}% >= {self.threshold}%)",
                    data=results,
                    exit_code=ExitCode.SUCCESS
                )
            else:
                return CLIOutput(
                    success=False,
                    message=f"Quality gate failed ({current_quality}% < {self.threshold}%)",
                    data=results,
                    errors=[f"Quality score below threshold"],
                    exit_code=ExitCode.ERROR
                )

        except Exception as e:
            return CLIOutput(
                success=False,
                message="Quality gate check failed",
                errors=[str(e)],
                exit_code=ExitCode.ERROR
            )

    def run(self) -> None:
        """Execute command and print output."""
        output = self.execute()
        self.formatter.print_output(output)


class StatusCommand(BaseCLICommand):
    """
    Example: Fleet status command with CI/CD support.

    Usage:
        # Standard status
        aqe status

        # JSON output for CI
        aqe status --json
    """

    def __init__(self, **cli_options):
        """Initialize status command."""
        super().__init__(**cli_options)
        self.formatter = OutputFormatter(
            json_format=self.json_output,
            quiet=self.quiet
        )

    def execute(self) -> CLIOutput:
        """
        Get fleet status.

        Returns:
            CLIOutput with status
        """
        try:
            status = {
                "fleet": {
                    "healthy": True,
                    "activeAgents": 5,
                    "totalAgents": 19
                },
                "agents": [
                    {"id": "test-gen-1", "status": "idle", "tasks": 0},
                    {"id": "coverage-1", "status": "running", "tasks": 2},
                    {"id": "security-1", "status": "idle", "tasks": 0}
                ],
                "resources": {
                    "cpuUsage": 45.2,
                    "memoryUsage": 1024,
                    "activeTasks": 2
                }
            }

            return CLIOutput(
                success=True,
                message="Fleet is healthy",
                data=status,
                exit_code=ExitCode.SUCCESS
            )

        except Exception as e:
            return CLIOutput(
                success=False,
                message="Failed to get fleet status",
                errors=[str(e)],
                exit_code=ExitCode.ERROR
            )

    def run(self) -> None:
        """Execute command and print output."""
        output = self.execute()
        self.formatter.print_output(output)
