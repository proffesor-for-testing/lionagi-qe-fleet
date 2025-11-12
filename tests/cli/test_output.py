"""
Tests for output formatting functionality.
"""

import json
import pytest
from io import StringIO
from unittest.mock import patch
from lionagi_qe.cli.output import OutputFormatter
from lionagi_qe.cli.base import CLIOutput, ExitCode


class TestOutputFormatter:
    """Test OutputFormatter class."""

    def test_initialization_default(self):
        """Test default initialization."""
        formatter = OutputFormatter()

        assert formatter.json_format is False
        assert formatter.quiet is False
        assert formatter.color is True

    def test_initialization_json_mode(self):
        """Test initialization with JSON mode."""
        formatter = OutputFormatter(json_format=True)

        assert formatter.json_format is True
        assert formatter.color is False  # Color disabled in JSON mode

    def test_initialization_quiet_mode(self):
        """Test initialization with quiet mode."""
        formatter = OutputFormatter(quiet=True)

        assert formatter.quiet is True

    def test_format_json_output_success(self):
        """Test JSON output formatting for success."""
        formatter = OutputFormatter(json_format=True)
        output = CLIOutput(
            success=True,
            message="Test successful",
            data={"count": 42}
        )

        result = formatter.format_output(output)
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["message"] == "Test successful"
        assert parsed["data"]["count"] == 42
        assert parsed["exitCode"] == 0

    def test_format_json_output_error(self):
        """Test JSON output formatting for error."""
        formatter = OutputFormatter(json_format=True)
        output = CLIOutput(
            success=False,
            message="Test failed",
            errors=["Error 1", "Error 2"]
        )

        result = formatter.format_output(output)
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["message"] == "Test failed"
        assert len(parsed["errors"]) == 2
        assert parsed["exitCode"] == 1

    def test_format_text_output_success(self):
        """Test text output formatting for success."""
        formatter = OutputFormatter(json_format=False, color=False)
        output = CLIOutput(
            success=True,
            message="Test successful"
        )

        result = formatter.format_output(output)

        assert "SUCCESS" in result
        assert "Test successful" in result

    def test_format_text_output_with_warnings(self):
        """Test text output formatting with warnings."""
        formatter = OutputFormatter(json_format=False, color=False)
        output = CLIOutput(
            success=True,
            message="Test completed",
            warnings=["Warning 1", "Warning 2"]
        )

        result = formatter.format_output(output)

        assert "SUCCESS" in result
        assert "Warnings:" in result
        assert "Warning 1" in result
        assert "Warning 2" in result

    def test_format_text_output_with_errors(self):
        """Test text output formatting with errors."""
        formatter = OutputFormatter(json_format=False, color=False)
        output = CLIOutput(
            success=False,
            message="Test failed",
            errors=["Error 1"]
        )

        result = formatter.format_output(output)

        assert "FAILED" in result
        assert "Errors:" in result
        assert "Error 1" in result

    def test_format_text_output_quiet_mode(self):
        """Test text output formatting in quiet mode."""
        formatter = OutputFormatter(json_format=False, quiet=True, color=False)
        output = CLIOutput(
            success=True,
            message="Test successful",
            data={"count": 42}
        )

        result = formatter.format_output(output)

        # In quiet mode, should not show data
        assert "count" not in result

    def test_format_text_output_quiet_mode_with_errors(self):
        """Test text output formatting in quiet mode with errors."""
        formatter = OutputFormatter(json_format=False, quiet=True, color=False)
        output = CLIOutput(
            success=False,
            errors=["Critical error"]
        )

        result = formatter.format_output(output)

        # Errors should always be shown
        assert "Critical error" in result

    def test_format_data_simple(self):
        """Test _format_data with simple data."""
        formatter = OutputFormatter(color=False)
        data = {"key1": "value1", "key2": 42}

        result = formatter._format_data(data)

        assert "key1:" in result
        assert "value1" in result
        assert "key2:" in result
        assert "42" in result

    def test_format_data_nested(self):
        """Test _format_data with nested data."""
        formatter = OutputFormatter(color=False)
        data = {
            "outer": {
                "inner": "value"
            }
        }

        result = formatter._format_data(data)

        assert "outer:" in result
        assert "inner:" in result
        assert "value" in result

    def test_format_data_with_list(self):
        """Test _format_data with list."""
        formatter = OutputFormatter(color=False)
        data = {
            "items": ["item1", "item2", "item3"]
        }

        result = formatter._format_data(data)

        assert "items:" in result
        assert "item1" in result
        assert "item2" in result
        assert "item3" in result

    def test_print_output(self):
        """Test print_output exits with correct code."""
        formatter = OutputFormatter(json_format=True)
        output = CLIOutput(
            success=True,
            message="Test",
            exit_code=ExitCode.SUCCESS
        )

        with pytest.raises(SystemExit) as exc_info:
            formatter.print_output(output)

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_print_error(self):
        """Test print_error exits with error code."""
        formatter = OutputFormatter(json_format=True)

        with pytest.raises(SystemExit) as exc_info:
            formatter.print_error("Test error")

        assert exc_info.value.code == ExitCode.ERROR

    def test_print_success(self):
        """Test print_success exits with success code."""
        formatter = OutputFormatter(json_format=True)

        with pytest.raises(SystemExit) as exc_info:
            formatter.print_success("Test success")

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_print_success_with_warnings(self):
        """Test print_success with warnings exits with warning code."""
        formatter = OutputFormatter(json_format=True)

        with pytest.raises(SystemExit) as exc_info:
            formatter.print_success(
                "Test success",
                warnings=["Warning 1"]
            )

        assert exc_info.value.code == ExitCode.WARNING

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_normal_mode(self, mock_stdout):
        """Test print_progress in normal mode."""
        formatter = OutputFormatter(json_format=False, quiet=False, color=False)

        formatter.print_progress("Processing...")

        output = mock_stdout.getvalue()
        assert "Processing..." in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_quiet_mode(self, mock_stdout):
        """Test print_progress in quiet mode (should not print)."""
        formatter = OutputFormatter(json_format=False, quiet=True)

        formatter.print_progress("Processing...")

        output = mock_stdout.getvalue()
        assert output == ""

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_json_mode(self, mock_stdout):
        """Test print_progress in JSON mode (should not print)."""
        formatter = OutputFormatter(json_format=True)

        formatter.print_progress("Processing...")

        output = mock_stdout.getvalue()
        assert output == ""

    def test_color_codes_enabled(self):
        """Test that color codes are present when color is enabled."""
        formatter = OutputFormatter(color=True)

        assert formatter.COLORS["red"] != ""
        assert formatter.COLORS["green"] != ""
        assert formatter.COLORS["reset"] != ""

    def test_color_codes_disabled(self):
        """Test that color codes are empty when color is disabled."""
        formatter = OutputFormatter(color=False)

        assert formatter.COLORS["red"] == ""
        assert formatter.COLORS["green"] == ""
        assert formatter.COLORS["reset"] == ""


class TestOutputFormatterIntegration:
    """Integration tests for output formatting."""

    def test_json_output_can_be_parsed(self):
        """Test that JSON output can be parsed by json module."""
        formatter = OutputFormatter(json_format=True)
        output = CLIOutput(
            success=True,
            message="Test",
            data={"key": "value"}
        )

        result = formatter.format_output(output)
        parsed = json.loads(result)  # Should not raise

        assert isinstance(parsed, dict)
        assert "success" in parsed
        assert "data" in parsed

    def test_ci_mode_output_formatting(self):
        """Test output formatting optimized for CI mode."""
        # CI mode: JSON + quiet
        formatter = OutputFormatter(json_format=True, quiet=True)

        output = CLIOutput(
            success=True,
            message="Operation completed",
            data={"tests": 42, "coverage": 85.5}
        )

        result = formatter.format_output(output)
        parsed = json.loads(result)

        # Should have all essential data
        assert parsed["success"] is True
        assert parsed["data"]["tests"] == 42
        assert parsed["data"]["coverage"] == 85.5

        # Should be valid JSON
        json.dumps(parsed)  # Should not raise
