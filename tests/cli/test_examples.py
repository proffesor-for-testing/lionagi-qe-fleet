"""
Tests for example CLI command implementations.
"""

import pytest
from lionagi_qe.cli.examples import (
    TestGenerateCommand,
    QualityGateCommand,
    StatusCommand
)
from lionagi_qe.cli.base import ExitCode


class TestTestGenerateCommand:
    """Test TestGenerateCommand implementation."""

    def test_initialization(self):
        """Test command initialization."""
        cmd = TestGenerateCommand(
            target_path="src/",
            framework="pytest",
            ci_mode=True
        )

        assert cmd.target_path == "src/"
        assert cmd.framework == "pytest"
        assert cmd.ci_mode is True

    def test_execute_success(self):
        """Test successful test generation."""
        cmd = TestGenerateCommand(
            target_path="src/",
            framework="pytest",
            json_output=True
        )

        output = cmd.execute()

        assert output.success is True
        assert output.data["testsGenerated"] == 42
        assert output.data["framework"] == "pytest"
        assert "files" in output.data

    def test_execute_with_warnings(self):
        """Test execution with warnings (low coverage)."""
        cmd = TestGenerateCommand(
            target_path="src/",
            framework="pytest"
        )

        output = cmd.execute()

        # Coverage is 85.5%, below target 90%
        assert output.success is True
        assert len(output.warnings) > 0
        assert output.exit_code == ExitCode.WARNING

    def test_execute_invalid_input_non_interactive(self):
        """Test execution with invalid input in non-interactive mode."""
        cmd = TestGenerateCommand(
            target_path="",  # Empty path
            framework="pytest",
            non_interactive=True
        )

        output = cmd.execute()

        assert output.success is False
        assert output.exit_code == ExitCode.INVALID_INPUT
        assert len(output.errors) > 0

    def test_execute_json_output(self):
        """Test execution with JSON output enabled."""
        cmd = TestGenerateCommand(
            target_path="src/",
            framework="pytest",
            json_output=True
        )

        output = cmd.execute()

        # Should return structured data
        assert isinstance(output.data, dict)
        assert "testsGenerated" in output.data
        assert "coverage" in output.data


class TestQualityGateCommand:
    """Test QualityGateCommand implementation."""

    def test_initialization(self):
        """Test command initialization."""
        cmd = QualityGateCommand(
            threshold=80.0,
            ci_mode=True
        )

        assert cmd.threshold == 80.0
        assert cmd.ci_mode is True

    def test_execute_pass(self):
        """Test quality gate passing."""
        cmd = QualityGateCommand(
            threshold=80.0,
            json_output=True
        )

        output = cmd.execute()

        # Current quality is 85.5%, above threshold 80%
        assert output.success is True
        assert output.data["passed"] is True
        assert output.exit_code == ExitCode.SUCCESS

    def test_execute_fail(self):
        """Test quality gate failing."""
        cmd = QualityGateCommand(
            threshold=90.0,  # Higher than current 85.5%
            json_output=True
        )

        output = cmd.execute()

        # Current quality is 85.5%, below threshold 90%
        assert output.success is False
        assert output.data["passed"] is False
        assert output.exit_code == ExitCode.ERROR

    def test_execute_data_structure(self):
        """Test quality gate output data structure."""
        cmd = QualityGateCommand(threshold=80.0)

        output = cmd.execute()

        assert "currentQuality" in output.data
        assert "threshold" in output.data
        assert "passed" in output.data
        assert "checks" in output.data

        # Check individual checks
        checks = output.data["checks"]
        assert "coverage" in checks
        assert "complexity" in checks
        assert "duplication" in checks
        assert "security" in checks


class TestStatusCommand:
    """Test StatusCommand implementation."""

    def test_initialization(self):
        """Test command initialization."""
        cmd = StatusCommand(ci_mode=True)

        assert cmd.ci_mode is True

    def test_execute_success(self):
        """Test successful status retrieval."""
        cmd = StatusCommand(json_output=True)

        output = cmd.execute()

        assert output.success is True
        assert output.exit_code == ExitCode.SUCCESS

    def test_execute_data_structure(self):
        """Test status output data structure."""
        cmd = StatusCommand(json_output=True)

        output = cmd.execute()

        assert "fleet" in output.data
        assert "agents" in output.data
        assert "resources" in output.data

        # Check fleet status
        fleet = output.data["fleet"]
        assert "healthy" in fleet
        assert "activeAgents" in fleet
        assert "totalAgents" in fleet

        # Check resources
        resources = output.data["resources"]
        assert "cpuUsage" in resources
        assert "memoryUsage" in resources

    def test_execute_quiet_mode(self):
        """Test status in quiet mode."""
        cmd = StatusCommand(quiet=True)

        output = cmd.execute()

        # Should still return data
        assert output.success is True
        assert output.data is not None


class TestCommandIntegration:
    """Integration tests for CLI commands."""

    def test_ci_mode_workflow(self):
        """Test complete CI mode workflow."""
        # Generate tests
        gen_cmd = TestGenerateCommand(
            target_path="src/",
            framework="pytest",
            ci_mode=True
        )
        gen_output = gen_cmd.execute()

        assert gen_output.success is True

        # Check quality gate
        gate_cmd = QualityGateCommand(
            threshold=80.0,
            ci_mode=True
        )
        gate_output = gate_cmd.execute()

        assert gate_output.success is True

        # Get status
        status_cmd = StatusCommand(ci_mode=True)
        status_output = status_cmd.execute()

        assert status_output.success is True

    def test_commands_return_consistent_structure(self):
        """Test that all commands return consistent output structure."""
        commands = [
            TestGenerateCommand("src/", ci_mode=True),
            QualityGateCommand(80.0, ci_mode=True),
            StatusCommand(ci_mode=True),
        ]

        for cmd in commands:
            output = cmd.execute()

            # All should have these fields
            assert hasattr(output, "success")
            assert hasattr(output, "data")
            assert hasattr(output, "message")
            assert hasattr(output, "warnings")
            assert hasattr(output, "errors")
            assert hasattr(output, "exit_code")

    def test_json_output_is_serializable(self):
        """Test that JSON output can be serialized."""
        import json

        commands = [
            TestGenerateCommand("src/", json_output=True),
            QualityGateCommand(80.0, json_output=True),
            StatusCommand(json_output=True),
        ]

        for cmd in commands:
            output = cmd.execute()
            output_dict = output.to_dict()

            # Should be JSON serializable
            json_str = json.dumps(output_dict)
            assert isinstance(json_str, str)

            # Should be parseable
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
