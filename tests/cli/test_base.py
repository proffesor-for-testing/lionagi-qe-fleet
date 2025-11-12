"""
Tests for base CLI functionality including exit codes and command structure.
"""

import pytest
from lionagi_qe.cli.base import BaseCLICommand, CLIOutput, ExitCode


class TestExitCode:
    """Test exit code enum."""

    def test_exit_code_values(self):
        """Test that exit codes have correct values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.ERROR == 1
        assert ExitCode.WARNING == 2
        assert ExitCode.INVALID_INPUT == 3
        assert ExitCode.TIMEOUT == 4
        assert ExitCode.PERMISSION == 5
        assert ExitCode.NOT_FOUND == 6
        assert ExitCode.CONFLICT == 7

    def test_exit_code_is_int(self):
        """Test that exit codes are integers."""
        assert isinstance(ExitCode.SUCCESS, int)
        assert isinstance(ExitCode.ERROR, int)


class TestCLIOutput:
    """Test CLIOutput dataclass."""

    def test_cli_output_success(self):
        """Test successful CLI output."""
        output = CLIOutput(
            success=True,
            message="Operation successful",
            data={"count": 42}
        )

        assert output.success is True
        assert output.message == "Operation successful"
        assert output.data == {"count": 42}
        assert output.warnings == []
        assert output.errors == []
        assert output.exit_code == ExitCode.SUCCESS

    def test_cli_output_with_errors(self):
        """Test CLI output with errors auto-sets exit code."""
        output = CLIOutput(
            success=False,
            message="Operation failed",
            errors=["Error 1", "Error 2"]
        )

        assert output.success is False
        assert len(output.errors) == 2
        assert output.exit_code == ExitCode.ERROR

    def test_cli_output_with_warnings(self):
        """Test CLI output with warnings auto-sets exit code."""
        output = CLIOutput(
            success=True,
            message="Operation completed with warnings",
            warnings=["Warning 1"]
        )

        assert output.success is True
        assert len(output.warnings) == 1
        assert output.exit_code == ExitCode.WARNING

    def test_cli_output_to_dict(self):
        """Test CLI output conversion to dictionary."""
        output = CLIOutput(
            success=True,
            message="Test message",
            data={"key": "value"},
            warnings=["Warning"],
            errors=[]
        )

        result = output.to_dict()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["message"] == "Test message"
        assert result["data"] == {"key": "value"}
        assert result["warnings"] == ["Warning"]
        assert result["errors"] == []
        assert result["exitCode"] == ExitCode.WARNING

    def test_cli_output_explicit_exit_code(self):
        """Test that explicit exit code is preserved."""
        output = CLIOutput(
            success=False,
            message="Not found",
            errors=["Resource not found"],
            exit_code=ExitCode.NOT_FOUND
        )

        assert output.exit_code == ExitCode.NOT_FOUND


class TestBaseCLICommand:
    """Test BaseCLICommand class."""

    def test_default_initialization(self):
        """Test default initialization."""
        cmd = BaseCLICommand()

        assert cmd.json_output is False
        assert cmd.quiet is False
        assert cmd.non_interactive is False
        assert cmd.ci_mode is False

    def test_ci_mode_enables_all_flags(self):
        """Test that CI mode enables json, quiet, and non-interactive."""
        cmd = BaseCLICommand(ci_mode=True)

        assert cmd.json_output is True
        assert cmd.quiet is True
        assert cmd.non_interactive is True
        assert cmd.ci_mode is True

    def test_individual_flags(self):
        """Test individual flag initialization."""
        cmd = BaseCLICommand(
            json_output=True,
            quiet=True,
            non_interactive=False
        )

        assert cmd.json_output is True
        assert cmd.quiet is True
        assert cmd.non_interactive is False
        assert cmd.ci_mode is False

    def test_should_print_info_level(self):
        """Test should_print for info level."""
        cmd_normal = BaseCLICommand(quiet=False)
        cmd_quiet = BaseCLICommand(quiet=True)

        assert cmd_normal.should_print("info") is True
        assert cmd_quiet.should_print("info") is False

    def test_should_print_error_level(self):
        """Test should_print for error level."""
        cmd_normal = BaseCLICommand(quiet=False)
        cmd_quiet = BaseCLICommand(quiet=True)

        assert cmd_normal.should_print("error") is True
        assert cmd_quiet.should_print("error") is True

    def test_should_print_warning_level(self):
        """Test should_print for warning level."""
        cmd_normal = BaseCLICommand(quiet=False)
        cmd_quiet = BaseCLICommand(quiet=True)

        assert cmd_normal.should_print("warning") is True
        assert cmd_quiet.should_print("warning") is True

    def test_prompt_user_interactive(self):
        """Test prompt_user in interactive mode (with default)."""
        from unittest.mock import patch

        cmd = BaseCLICommand(non_interactive=False)

        # Mock input to avoid blocking
        with patch('builtins.input', return_value="user_input"):
            result = cmd.prompt_user("Enter value", default="default_value")
            assert result == "user_input"

        # Test fallback to default on EOFError
        with patch('builtins.input', side_effect=EOFError):
            result = cmd.prompt_user("Enter value", default="default_value")
            assert result == "default_value"

    def test_prompt_user_non_interactive_with_default(self):
        """Test prompt_user in non-interactive mode with default."""
        cmd = BaseCLICommand(non_interactive=True)

        result = cmd.prompt_user("Enter value", default="default_value")

        assert result == "default_value"

    def test_prompt_user_non_interactive_without_default(self):
        """Test prompt_user in non-interactive mode without default raises error."""
        cmd = BaseCLICommand(non_interactive=True)

        with pytest.raises(RuntimeError, match="Cannot prompt in non-interactive mode"):
            cmd.prompt_user("Enter value")

    def test_validate_required_input_valid(self):
        """Test validate_required_input with valid value."""
        cmd = BaseCLICommand(non_interactive=True)

        result = cmd.validate_required_input("param", "value")

        assert result == "value"

    def test_validate_required_input_none_non_interactive(self):
        """Test validate_required_input with None in non-interactive mode."""
        cmd = BaseCLICommand(non_interactive=True)

        with pytest.raises(ValueError, match="Required parameter 'param' is missing"):
            cmd.validate_required_input("param", None)

    def test_validate_required_input_empty_string_non_interactive(self):
        """Test validate_required_input with empty string in non-interactive mode."""
        cmd = BaseCLICommand(non_interactive=True)

        with pytest.raises(ValueError, match="Required parameter 'param' is missing"):
            cmd.validate_required_input("param", "   ")

    def test_validate_required_input_interactive_mode_allows_none(self):
        """Test validate_required_input with None in interactive mode."""
        cmd = BaseCLICommand(non_interactive=False)

        # In interactive mode, None is allowed (would prompt user)
        result = cmd.validate_required_input("param", None)

        assert result is None


class TestCLICommandIntegration:
    """Integration tests for CLI command behavior."""

    def test_ci_mode_workflow(self):
        """Test complete CI mode workflow."""
        cmd = BaseCLICommand(ci_mode=True)

        # Should not print info messages
        assert cmd.should_print("info") is False

        # Should print errors
        assert cmd.should_print("error") is True

        # Should use default values
        result = cmd.prompt_user("Test prompt", default="default")
        assert result == "default"

        # Should fail on missing required input
        with pytest.raises(ValueError):
            cmd.validate_required_input("required_param", None)

    def test_standard_mode_workflow(self):
        """Test standard interactive mode workflow."""
        cmd = BaseCLICommand()

        # Should print all messages
        assert cmd.should_print("info") is True
        assert cmd.should_print("error") is True

        # Should allow None values (would prompt)
        result = cmd.validate_required_input("param", None)
        assert result is None
