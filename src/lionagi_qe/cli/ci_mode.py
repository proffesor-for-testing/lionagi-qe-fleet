"""
CI mode configuration and utilities.

Provides CI-specific configuration and helpers.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CIModeConfig:
    """
    Configuration for CI/CD mode.

    Attributes:
        enabled: Whether CI mode is enabled
        json_output: Output in JSON format
        quiet: Minimal output
        non_interactive: No user prompts
        color: Enable color output (auto-disabled in CI)
        timeout: Default timeout for operations (seconds)
        max_retries: Maximum retries for failed operations
    """
    enabled: bool = False
    json_output: bool = True
    quiet: bool = True
    non_interactive: bool = True
    color: bool = False
    timeout: int = 300
    max_retries: int = 3

    @classmethod
    def from_environment(cls) -> "CIModeConfig":
        """
        Create CI mode config from environment variables.

        Detects common CI environment variables:
        - CI=true
        - CONTINUOUS_INTEGRATION=true
        - GITHUB_ACTIONS=true
        - GITLAB_CI=true
        - JENKINS_HOME=<path>
        - BUILDKITE=true
        - CIRCLECI=true
        - TRAVIS=true

        Returns:
            CIModeConfig instance
        """
        # Detect if running in CI
        ci_indicators = [
            os.getenv("CI") == "true",
            os.getenv("CONTINUOUS_INTEGRATION") == "true",
            os.getenv("GITHUB_ACTIONS") == "true",
            os.getenv("GITLAB_CI") == "true",
            os.getenv("JENKINS_HOME") is not None,
            os.getenv("BUILDKITE") == "true",
            os.getenv("CIRCLECI") == "true",
            os.getenv("TRAVIS") == "true",
        ]

        enabled = any(ci_indicators)

        # Read configuration from environment
        return cls(
            enabled=enabled,
            json_output=os.getenv("AQE_JSON_OUTPUT", str(enabled)).lower() == "true",
            quiet=os.getenv("AQE_QUIET", str(enabled)).lower() == "true",
            non_interactive=os.getenv("AQE_NON_INTERACTIVE", str(enabled)).lower() == "true",
            color=os.getenv("AQE_COLOR", "false").lower() == "true",
            timeout=int(os.getenv("AQE_TIMEOUT", "300")),
            max_retries=int(os.getenv("AQE_MAX_RETRIES", "3")),
        )

    @classmethod
    def create(
        cls,
        ci_mode: bool = False,
        json_output: Optional[bool] = None,
        quiet: Optional[bool] = None,
        non_interactive: Optional[bool] = None,
        **kwargs
    ) -> "CIModeConfig":
        """
        Create CI mode config with overrides.

        Args:
            ci_mode: Enable CI mode (sets defaults)
            json_output: Override JSON output
            quiet: Override quiet mode
            non_interactive: Override non-interactive mode
            **kwargs: Additional config overrides

        Returns:
            CIModeConfig instance
        """
        if ci_mode:
            config = cls(enabled=True, **kwargs)
        else:
            config = cls.from_environment()

        # Apply overrides
        if json_output is not None:
            config.json_output = json_output
        if quiet is not None:
            config.quiet = quiet
        if non_interactive is not None:
            config.non_interactive = non_interactive

        return config

    def to_dict(self):
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "jsonOutput": self.json_output,
            "quiet": self.quiet,
            "nonInteractive": self.non_interactive,
            "color": self.color,
            "timeout": self.timeout,
            "maxRetries": self.max_retries,
        }


def is_ci_environment() -> bool:
    """
    Check if running in a CI environment.

    Returns:
        True if CI environment detected
    """
    return CIModeConfig.from_environment().enabled


def get_ci_platform() -> Optional[str]:
    """
    Detect CI platform.

    Returns:
        CI platform name or None
    """
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "github-actions"
    elif os.getenv("GITLAB_CI") == "true":
        return "gitlab-ci"
    elif os.getenv("JENKINS_HOME"):
        return "jenkins"
    elif os.getenv("BUILDKITE") == "true":
        return "buildkite"
    elif os.getenv("CIRCLECI") == "true":
        return "circleci"
    elif os.getenv("TRAVIS") == "true":
        return "travis-ci"
    elif os.getenv("CI") == "true":
        return "generic-ci"
    return None
