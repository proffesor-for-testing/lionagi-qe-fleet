"""Centralized hook system for QE fleet observability

This module provides comprehensive observability for the QE Fleet through LionAGI's
hook system. It tracks all AI model invocations, costs, and metrics across the fleet.

Features:
    - Real-time AI call logging
    - Per-agent cost tracking
    - Token usage monitoring
    - Comprehensive metrics aggregation
    - Cost alert thresholds
"""

from lionagi.service.hooks import HookRegistry, HookEventTypes
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import json


class QEHooks:
    """Centralized hooks for QE fleet observability

    This class implements the hook system for tracking all AI model interactions
    in the QE Fleet. It provides:

    - Pre-invocation logging: Logs details before each AI call
    - Post-invocation tracking: Records costs, tokens, and metrics after each call
    - Per-agent cost breakdown: Tracks spending by individual agents
    - Alert system: Warns when cost thresholds are exceeded

    Example:
        >>> hooks = QEHooks(fleet_id="production-fleet")
        >>> registry = hooks.create_registry()
        >>> model = iModel(provider="openai", model="gpt-4", hook_registry=registry)
        >>> # Use model for AI calls
        >>> metrics = hooks.get_metrics()
        >>> print(f"Total cost: ${metrics['total_cost']:.4f}")
    """

    def __init__(
        self,
        fleet_id: str,
        cost_alert_threshold: float = 10.0,
        enable_detailed_logging: bool = True
    ):
        """Initialize QE hooks system

        Args:
            fleet_id: Unique identifier for this fleet instance
            cost_alert_threshold: Dollar amount that triggers cost warnings
            enable_detailed_logging: Whether to log detailed information for each call
        """
        self.fleet_id = fleet_id
        self.cost_alert_threshold = cost_alert_threshold
        self.enable_detailed_logging = enable_detailed_logging

        # Setup logging
        self.logger = logging.getLogger(f"qe_fleet.hooks.{fleet_id}")

        # Cost tracking
        self.cost_tracker = {
            "total": 0.0,
            "by_agent": {},
            "by_model": {},
            "by_provider": {}
        }

        # Call tracking
        self.call_count = 0
        self.call_history = []

        # Token tracking
        self.token_usage = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0
        }

        # Session tracking
        self.session_start = datetime.utcnow()

        # Alert tracking
        self.alerts_triggered = []

    async def pre_invocation_hook(self, event, **kwargs):
        """Hook called before each AI model invocation

        Logs information about the upcoming AI call including:
        - Call number
        - Provider and model
        - Agent making the call
        - Context information

        Args:
            event: Hook event containing invocation details
            **kwargs: Additional context passed to the hook
        """
        self.call_count += 1

        # Extract context
        context = kwargs.get('context', {})
        agent_id = context.get('agent_id', 'unknown')
        task_type = context.get('task_type', 'unknown')

        # Get model information
        provider = getattr(event, 'provider', 'unknown')
        model = getattr(event, 'model', 'unknown')

        # Log the call
        log_message = (
            f"AI Call #{self.call_count}: "
            f"{provider}/{model} "
            f"- Agent: {agent_id} "
            f"- Task: {task_type}"
        )

        if self.enable_detailed_logging:
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)

        # Store call details for history
        call_details = {
            "call_number": self.call_count,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "model": model,
            "agent_id": agent_id,
            "task_type": task_type,
            "phase": "pre_invocation"
        }

        self.call_history.append(call_details)

    async def post_invocation_hook(self, event, **kwargs):
        """Hook called after each AI model invocation

        Tracks and aggregates:
        - Token usage (input, output, total)
        - Cost per call
        - Cost by agent, model, and provider
        - Response metrics

        Triggers cost alerts if threshold is exceeded.

        Args:
            event: Hook event containing response details
            **kwargs: Additional context passed to the hook
        """
        # Extract context
        context = kwargs.get('context', {})
        agent_id = context.get('agent_id', 'unknown')

        # Get usage information
        usage = getattr(event, 'usage', None)
        if usage is None:
            self.logger.warning(f"No usage information in post-invocation event for call #{self.call_count}")
            return

        # Extract token counts
        input_tokens = getattr(usage, 'prompt_tokens', 0) or getattr(usage, 'input_tokens', 0)
        output_tokens = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0)
        total_tokens = getattr(usage, 'total_tokens', input_tokens + output_tokens)

        # Calculate cost (if available from usage object)
        cost = getattr(usage, 'total_cost', None)

        # If cost not provided, estimate based on model
        if cost is None:
            provider = getattr(event, 'provider', 'unknown')
            model = getattr(event, 'model', 'unknown')
            cost = self._estimate_cost(provider, model, input_tokens, output_tokens)

        # Update cost trackers
        self.cost_tracker["total"] += cost

        # Track by agent
        if agent_id not in self.cost_tracker["by_agent"]:
            self.cost_tracker["by_agent"][agent_id] = {
                "total_cost": 0.0,
                "call_count": 0,
                "total_tokens": 0
            }
        self.cost_tracker["by_agent"][agent_id]["total_cost"] += cost
        self.cost_tracker["by_agent"][agent_id]["call_count"] += 1
        self.cost_tracker["by_agent"][agent_id]["total_tokens"] += total_tokens

        # Track by model
        model_key = f"{getattr(event, 'provider', 'unknown')}/{getattr(event, 'model', 'unknown')}"
        if model_key not in self.cost_tracker["by_model"]:
            self.cost_tracker["by_model"][model_key] = {
                "total_cost": 0.0,
                "call_count": 0,
                "total_tokens": 0
            }
        self.cost_tracker["by_model"][model_key]["total_cost"] += cost
        self.cost_tracker["by_model"][model_key]["call_count"] += 1
        self.cost_tracker["by_model"][model_key]["total_tokens"] += total_tokens

        # Track by provider
        provider = getattr(event, 'provider', 'unknown')
        if provider not in self.cost_tracker["by_provider"]:
            self.cost_tracker["by_provider"][provider] = {
                "total_cost": 0.0,
                "call_count": 0,
                "total_tokens": 0
            }
        self.cost_tracker["by_provider"][provider]["total_cost"] += cost
        self.cost_tracker["by_provider"][provider]["call_count"] += 1
        self.cost_tracker["by_provider"][provider]["total_tokens"] += total_tokens

        # Update token usage
        self.token_usage["total_input_tokens"] += input_tokens
        self.token_usage["total_output_tokens"] += output_tokens
        self.token_usage["total_tokens"] += total_tokens

        # Log the response
        log_message = (
            f"AI Response #{self.call_count}: "
            f"{total_tokens} tokens "
            f"({input_tokens} in, {output_tokens} out), "
            f"${cost:.4f} cost, "
            f"Agent: {agent_id}"
        )

        if self.enable_detailed_logging:
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)

        # Check cost alert threshold
        if self.cost_tracker["total"] >= self.cost_alert_threshold:
            self._trigger_cost_alert()

        # Update call history
        if self.call_history:
            # Update the last entry with post-invocation data
            self.call_history[-1].update({
                "phase": "post_invocation",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "cumulative_cost": self.cost_tracker["total"]
            })

    def _estimate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost based on provider pricing

        Args:
            provider: Provider name (openai, anthropic, etc.)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing per 1M tokens (approximate as of 2024)
        pricing = {
            "openai": {
                "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
                "gpt-4": {"input": 30.00, "output": 60.00},
                "gpt-4o": {"input": 5.00, "output": 15.00},
                "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
                "claude-3-haiku": {"input": 0.25, "output": 1.25},
                "claude-3-opus": {"input": 15.00, "output": 75.00},
            }
        }

        # Get pricing for this model
        model_pricing = pricing.get(provider, {}).get(model)

        if model_pricing is None:
            # Default to GPT-3.5 pricing if unknown
            self.logger.warning(f"Unknown pricing for {provider}/{model}, using default")
            model_pricing = {"input": 0.50, "output": 1.50}

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

        return input_cost + output_cost

    def _trigger_cost_alert(self):
        """Trigger a cost alert when threshold is exceeded"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_cost": self.cost_tracker["total"],
            "threshold": self.cost_alert_threshold,
            "call_count": self.call_count
        }

        # Only trigger once per threshold crossing
        if not self.alerts_triggered or self.alerts_triggered[-1]["total_cost"] < self.cost_alert_threshold:
            self.alerts_triggered.append(alert)
            self.logger.warning(
                f"Cost alert: Total cost ${self.cost_tracker['total']:.2f} "
                f"has exceeded threshold ${self.cost_alert_threshold:.2f}"
            )

    def create_registry(self) -> HookRegistry:
        """Create hook registry for attaching to models

        Returns:
            HookRegistry configured with pre and post invocation hooks

        Example:
            >>> hooks = QEHooks(fleet_id="test")
            >>> registry = hooks.create_registry()
            >>> model = iModel(provider="openai", model="gpt-4", hook_registry=registry)
        """
        return HookRegistry(hooks={
            HookEventTypes.PreInvocation: self.pre_invocation_hook,
            HookEventTypes.PostInvocation: self.post_invocation_hook
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for all AI calls

        Returns:
            Dictionary containing:
            - Total cost and breakdown by agent/model/provider
            - Token usage statistics
            - Call counts
            - Session duration
            - Cost efficiency metrics

        Example:
            >>> metrics = hooks.get_metrics()
            >>> print(f"Total spent: ${metrics['total_cost']:.2f}")
            >>> print(f"Average cost per call: ${metrics['average_cost_per_call']:.4f}")
        """
        session_duration = (datetime.utcnow() - self.session_start).total_seconds()

        metrics = {
            # Cost metrics
            "total_cost": self.cost_tracker["total"],
            "by_agent": self.cost_tracker["by_agent"],
            "by_model": self.cost_tracker["by_model"],
            "by_provider": self.cost_tracker["by_provider"],

            # Call metrics
            "total_calls": self.call_count,
            "average_cost_per_call": (
                self.cost_tracker["total"] / self.call_count
                if self.call_count > 0 else 0.0
            ),

            # Token metrics
            "token_usage": self.token_usage,
            "average_tokens_per_call": (
                self.token_usage["total_tokens"] / self.call_count
                if self.call_count > 0 else 0
            ),

            # Session metrics
            "session_duration_seconds": session_duration,
            "calls_per_minute": (
                (self.call_count / session_duration) * 60
                if session_duration > 0 else 0
            ),
            "cost_per_minute": (
                (self.cost_tracker["total"] / session_duration) * 60
                if session_duration > 0 else 0
            ),

            # Alert metrics
            "alerts_triggered": len(self.alerts_triggered),
            "cost_alert_threshold": self.cost_alert_threshold,

            # Fleet info
            "fleet_id": self.fleet_id,
            "session_start": self.session_start.isoformat()
        }

        return metrics

    def get_call_count(self) -> int:
        """Get total number of AI calls made

        Returns:
            Number of AI model invocations
        """
        return self.call_count

    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific agent

        Args:
            agent_id: Agent identifier

        Returns:
            Metrics for the agent or None if not found
        """
        return self.cost_tracker["by_agent"].get(agent_id)

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format

        Args:
            format: Export format ('json', 'csv', 'summary')

        Returns:
            Formatted metrics string
        """
        metrics = self.get_metrics()

        if format == "json":
            return json.dumps(metrics, indent=2)

        elif format == "summary":
            summary = f"""
=== QE Fleet Metrics Summary ===
Fleet ID: {metrics['fleet_id']}
Session Duration: {metrics['session_duration_seconds']:.1f}s

Cost Metrics:
  Total Cost: ${metrics['total_cost']:.4f}
  Average per Call: ${metrics['average_cost_per_call']:.4f}
  Cost per Minute: ${metrics['cost_per_minute']:.4f}

Call Metrics:
  Total Calls: {metrics['total_calls']}
  Calls per Minute: {metrics['calls_per_minute']:.2f}

Token Usage:
  Total Tokens: {metrics['token_usage']['total_tokens']:,}
  Input Tokens: {metrics['token_usage']['total_input_tokens']:,}
  Output Tokens: {metrics['token_usage']['total_output_tokens']:,}
  Average per Call: {metrics['average_tokens_per_call']:.0f}

Top Agents by Cost:
"""
            # Add top agents
            top_agents = sorted(
                metrics['by_agent'].items(),
                key=lambda x: x[1]['total_cost'],
                reverse=True
            )[:5]

            for agent_id, agent_metrics in top_agents:
                summary += f"  {agent_id}: ${agent_metrics['total_cost']:.4f} ({agent_metrics['call_count']} calls)\n"

            return summary.strip()

        else:
            raise ValueError(f"Unsupported format: {format}")

    def reset_metrics(self):
        """Reset all metrics to zero

        Useful for starting a new measurement period.
        """
        self.cost_tracker = {
            "total": 0.0,
            "by_agent": {},
            "by_model": {},
            "by_provider": {}
        }
        self.call_count = 0
        self.call_history = []
        self.token_usage = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0
        }
        self.session_start = datetime.utcnow()
        self.alerts_triggered = []

        self.logger.info("Metrics reset")

    def get_call_history(self, limit: Optional[int] = None) -> list:
        """Get history of AI calls

        Args:
            limit: Maximum number of recent calls to return (None for all)

        Returns:
            List of call detail dictionaries
        """
        if limit is None:
            return self.call_history
        return self.call_history[-limit:]

    def dashboard_ascii(self) -> str:
        """Generate ASCII art dashboard of current metrics

        Returns:
            ASCII table with key metrics
        """
        metrics = self.get_metrics()

        dashboard = f"""
╔══════════════════════════════════════════════════════════════╗
║              QE Fleet Observability Dashboard                ║
╠══════════════════════════════════════════════════════════════╣
║ Fleet ID: {metrics['fleet_id']:<47} ║
║ Session Duration: {metrics['session_duration_seconds']:.1f}s{' ' * (40 - len(f"{metrics['session_duration_seconds']:.1f}s"))} ║
╠══════════════════════════════════════════════════════════════╣
║ COST METRICS                                                 ║
║   Total Cost:          ${metrics['total_cost']:>10.4f}                    ║
║   Avg Cost/Call:       ${metrics['average_cost_per_call']:>10.4f}                    ║
║   Cost/Minute:         ${metrics['cost_per_minute']:>10.4f}                    ║
╠══════════════════════════════════════════════════════════════╣
║ CALL METRICS                                                 ║
║   Total Calls:         {metrics['total_calls']:>10}                       ║
║   Calls/Minute:        {metrics['calls_per_minute']:>10.2f}                       ║
╠══════════════════════════════════════════════════════════════╣
║ TOKEN METRICS                                                ║
║   Total Tokens:        {metrics['token_usage']['total_tokens']:>10,}                       ║
║   Input Tokens:        {metrics['token_usage']['total_input_tokens']:>10,}                       ║
║   Output Tokens:       {metrics['token_usage']['total_output_tokens']:>10,}                       ║
║   Avg Tokens/Call:     {metrics['average_tokens_per_call']:>10.0f}                       ║
╠══════════════════════════════════════════════════════════════╣
║ ALERTS                                                       ║
║   Alerts Triggered:    {metrics['alerts_triggered']:>10}                       ║
║   Cost Threshold:      ${metrics['cost_alert_threshold']:>10.2f}                    ║
╚══════════════════════════════════════════════════════════════╝
"""
        return dashboard
