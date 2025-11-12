"""
Tests for CI mode configuration and detection.
"""

import os
import pytest
from unittest.mock import patch
from lionagi_qe.cli.ci_mode import (
    CIModeConfig,
    is_ci_environment,
    get_ci_platform
)


class TestCIModeConfig:
    """Test CIModeConfig dataclass."""

    def test_default_initialization(self):
        """Test default initialization."""
        config = CIModeConfig()

        assert config.enabled is False
        assert config.json_output is True
        assert config.quiet is True
        assert config.non_interactive is True
        assert config.color is False
        assert config.timeout == 300
        assert config.max_retries == 3

    def test_custom_initialization(self):
        """Test custom initialization."""
        config = CIModeConfig(
            enabled=True,
            timeout=600,
            max_retries=5
        )

        assert config.enabled is True
        assert config.timeout == 600
        assert config.max_retries == 5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = CIModeConfig(enabled=True, timeout=600)

        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["enabled"] is True
        assert result["timeout"] == 600
        assert "jsonOutput" in result
        assert "nonInteractive" in result

    @patch.dict(os.environ, {"CI": "true"})
    def test_from_environment_ci_detected(self):
        """Test from_environment when CI is detected."""
        config = CIModeConfig.from_environment()

        assert config.enabled is True
        assert config.json_output is True
        assert config.quiet is True
        assert config.non_interactive is True

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_from_environment_github_actions(self):
        """Test from_environment with GitHub Actions."""
        config = CIModeConfig.from_environment()

        assert config.enabled is True

    @patch.dict(os.environ, {"GITLAB_CI": "true"})
    def test_from_environment_gitlab_ci(self):
        """Test from_environment with GitLab CI."""
        config = CIModeConfig.from_environment()

        assert config.enabled is True

    @patch.dict(os.environ, {"JENKINS_HOME": "/var/jenkins"})
    def test_from_environment_jenkins(self):
        """Test from_environment with Jenkins."""
        config = CIModeConfig.from_environment()

        assert config.enabled is True

    @patch.dict(os.environ, {}, clear=True)
    def test_from_environment_no_ci(self):
        """Test from_environment when no CI is detected."""
        config = CIModeConfig.from_environment()

        assert config.enabled is False

    @patch.dict(os.environ, {
        "AQE_JSON_OUTPUT": "false",
        "AQE_QUIET": "false",
        "AQE_NON_INTERACTIVE": "false",
        "AQE_COLOR": "true",
        "AQE_TIMEOUT": "600",
        "AQE_MAX_RETRIES": "5"
    }, clear=True)
    def test_from_environment_with_overrides(self):
        """Test from_environment with environment variable overrides."""
        config = CIModeConfig.from_environment()

        assert config.json_output is False
        assert config.quiet is False
        assert config.non_interactive is False
        assert config.color is True
        assert config.timeout == 600
        assert config.max_retries == 5

    def test_create_ci_mode_enabled(self):
        """Test create with ci_mode=True."""
        config = CIModeConfig.create(ci_mode=True)

        assert config.enabled is True
        assert config.json_output is True
        assert config.quiet is True
        assert config.non_interactive is True

    def test_create_with_overrides(self):
        """Test create with individual overrides."""
        config = CIModeConfig.create(
            ci_mode=True,
            json_output=False,
            quiet=False
        )

        assert config.enabled is True
        assert config.json_output is False  # Overridden
        assert config.quiet is False  # Overridden
        assert config.non_interactive is True  # Not overridden

    @patch.dict(os.environ, {"CI": "true"})
    def test_create_from_environment_no_ci_mode(self):
        """Test create without ci_mode flag uses environment detection."""
        config = CIModeConfig.create(ci_mode=False)

        assert config.enabled is True  # Detected from environment


class TestCIDetection:
    """Test CI environment detection functions."""

    @patch.dict(os.environ, {"CI": "true"})
    def test_is_ci_environment_true(self):
        """Test is_ci_environment returns True when CI detected."""
        assert is_ci_environment() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_ci_environment_false(self):
        """Test is_ci_environment returns False when no CI detected."""
        assert is_ci_environment() is False

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_get_ci_platform_github_actions(self):
        """Test get_ci_platform for GitHub Actions."""
        assert get_ci_platform() == "github-actions"

    @patch.dict(os.environ, {"GITLAB_CI": "true"})
    def test_get_ci_platform_gitlab(self):
        """Test get_ci_platform for GitLab CI."""
        assert get_ci_platform() == "gitlab-ci"

    @patch.dict(os.environ, {"JENKINS_HOME": "/var/jenkins"})
    def test_get_ci_platform_jenkins(self):
        """Test get_ci_platform for Jenkins."""
        assert get_ci_platform() == "jenkins"

    @patch.dict(os.environ, {"BUILDKITE": "true"})
    def test_get_ci_platform_buildkite(self):
        """Test get_ci_platform for Buildkite."""
        assert get_ci_platform() == "buildkite"

    @patch.dict(os.environ, {"CIRCLECI": "true"})
    def test_get_ci_platform_circleci(self):
        """Test get_ci_platform for CircleCI."""
        assert get_ci_platform() == "circleci"

    @patch.dict(os.environ, {"TRAVIS": "true"})
    def test_get_ci_platform_travis(self):
        """Test get_ci_platform for Travis CI."""
        assert get_ci_platform() == "travis-ci"

    @patch.dict(os.environ, {"CI": "true"})
    def test_get_ci_platform_generic(self):
        """Test get_ci_platform for generic CI."""
        assert get_ci_platform() == "generic-ci"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_ci_platform_none(self):
        """Test get_ci_platform returns None when no CI detected."""
        assert get_ci_platform() is None


class TestCIModeIntegration:
    """Integration tests for CI mode configuration."""

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_github_actions_full_workflow(self):
        """Test complete workflow in GitHub Actions environment."""
        # Detect environment
        assert is_ci_environment() is True
        assert get_ci_platform() == "github-actions"

        # Create config
        config = CIModeConfig.from_environment()

        assert config.enabled is True
        assert config.json_output is True
        assert config.non_interactive is True

    @patch.dict(os.environ, {
        "CI": "true",
        "AQE_TIMEOUT": "900",
        "AQE_MAX_RETRIES": "10"
    })
    def test_ci_with_custom_settings(self):
        """Test CI mode with custom environment settings."""
        config = CIModeConfig.from_environment()

        assert config.enabled is True
        assert config.timeout == 900
        assert config.max_retries == 10

    def test_explicit_ci_mode_overrides_environment(self):
        """Test explicit ci_mode flag overrides environment."""
        with patch.dict(os.environ, {}, clear=True):
            # No CI in environment
            config = CIModeConfig.create(ci_mode=True)

            # But explicit flag enables it
            assert config.enabled is True
            assert config.json_output is True
