#!/usr/bin/env python3
"""Demonstration of QE Fleet Hooks System

This script demonstrates the observability features without requiring
actual LionAGI model calls. It shows:

1. Hook initialization
2. Simulated AI call tracking
3. Cost tracking by agent
4. Metrics reporting
5. Dashboard display
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock


# Mock the lionagi imports for demonstration
class MockHookRegistry:
    def __init__(self, hooks):
        self.hooks = hooks


class MockHookEventTypes:
    PreInvocation = "pre_invocation"
    PostInvocation = "post_invocation"


# Temporarily mock the imports
import sys
from unittest.mock import MagicMock

sys.modules['lionagi.service.hooks'] = MagicMock()
sys.modules['lionagi.service.hooks'].HookRegistry = MockHookRegistry
sys.modules['lionagi.service.hooks'].HookEventTypes = MockHookEventTypes

# Now we can import our hooks module
sys.path.insert(0, '/workspaces/lionagi-qe-fleet/src')
from lionagi_qe.core.hooks import QEHooks


async def simulate_ai_call(hooks, agent_id, provider, model, input_tokens, output_tokens):
    """Simulate an AI model call with hooks"""

    # Create mock event for pre-invocation
    pre_event = Mock()
    pre_event.provider = provider
    pre_event.model = model

    context = {
        "agent_id": agent_id,
        "task_type": "test-generation"
    }

    # Call pre-invocation hook
    await hooks.pre_invocation_hook(pre_event, context=context)

    # Simulate processing time
    await asyncio.sleep(0.01)

    # Create mock event for post-invocation
    post_event = Mock()
    post_event.provider = provider
    post_event.model = model

    usage = Mock()
    usage.prompt_tokens = input_tokens
    usage.completion_tokens = output_tokens
    usage.total_tokens = input_tokens + output_tokens
    usage.total_cost = None  # Let hooks estimate

    post_event.usage = usage

    # Call post-invocation hook
    await hooks.post_invocation_hook(post_event, context=context)


async def main():
    """Main demonstration"""

    print("=" * 70)
    print("QE Fleet Hooks System - Demonstration")
    print("=" * 70)
    print()

    # Initialize hooks
    print("1. Initializing hooks system...")
    hooks = QEHooks(
        fleet_id="demo-fleet",
        cost_alert_threshold=0.10,
        enable_detailed_logging=True
    )
    print(f"   ✓ Fleet ID: {hooks.fleet_id}")
    print(f"   ✓ Cost alert threshold: ${hooks.cost_alert_threshold}")
    print()

    # Simulate various AI calls
    print("2. Simulating AI model calls...")
    print()

    # Test Generator Agent - uses GPT-3.5 for simple tests
    print("   Test Generator Agent:")
    for i in range(5):
        await simulate_ai_call(
            hooks,
            agent_id="test-generator",
            provider="openai",
            model="gpt-3.5-turbo",
            input_tokens=500 + i * 50,
            output_tokens=800 + i * 100
        )
        print(f"     - Generated test case #{i+1}")

    # Coverage Analyzer - uses GPT-4 for complex analysis
    print("   Coverage Analyzer Agent:")
    for i in range(3):
        await simulate_ai_call(
            hooks,
            agent_id="coverage-analyzer",
            provider="openai",
            model="gpt-4",
            input_tokens=1000 + i * 100,
            output_tokens=600 + i * 50
        )
        print(f"     - Analyzed coverage report #{i+1}")

    # Security Scanner - uses Claude Sonnet for critical analysis
    print("   Security Scanner Agent:")
    for i in range(2):
        await simulate_ai_call(
            hooks,
            agent_id="security-scanner",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1500 + i * 200,
            output_tokens=1000 + i * 100
        )
        print(f"     - Performed security scan #{i+1}")

    print()
    print(f"   ✓ Total AI calls made: {hooks.get_call_count()}")
    print()

    # Display metrics
    print("3. Retrieving metrics...")
    metrics = hooks.get_metrics()
    print()

    print("   Cost Metrics:")
    print(f"     Total Cost: ${metrics['total_cost']:.4f}")
    print(f"     Average Cost per Call: ${metrics['average_cost_per_call']:.4f}")
    print(f"     Cost per Minute: ${metrics['cost_per_minute']:.4f}")
    print()

    print("   Call Metrics:")
    print(f"     Total Calls: {metrics['total_calls']}")
    print(f"     Calls per Minute: {metrics['calls_per_minute']:.2f}")
    print()

    print("   Token Metrics:")
    print(f"     Total Tokens: {metrics['token_usage']['total_tokens']:,}")
    print(f"     Input Tokens: {metrics['token_usage']['total_input_tokens']:,}")
    print(f"     Output Tokens: {metrics['token_usage']['total_output_tokens']:,}")
    print(f"     Average Tokens per Call: {metrics['average_tokens_per_call']:.0f}")
    print()

    # Display per-agent breakdown
    print("4. Per-Agent Cost Breakdown:")
    print()
    for agent_id, agent_metrics in metrics['by_agent'].items():
        print(f"   {agent_id}:")
        print(f"     Calls: {agent_metrics['call_count']}")
        print(f"     Cost: ${agent_metrics['total_cost']:.4f}")
        print(f"     Tokens: {agent_metrics['total_tokens']:,}")
        print(f"     Avg Cost/Call: ${agent_metrics['total_cost'] / agent_metrics['call_count']:.4f}")
        print()

    # Display per-model breakdown
    print("5. Per-Model Cost Breakdown:")
    print()
    for model_key, model_metrics in metrics['by_model'].items():
        print(f"   {model_key}:")
        print(f"     Calls: {model_metrics['call_count']}")
        print(f"     Cost: ${model_metrics['total_cost']:.4f}")
        print(f"     Tokens: {model_metrics['total_tokens']:,}")
        print()

    # Display cost summary
    print("6. Cost Summary:")
    print()
    summary = hooks.export_metrics(format="summary")
    print(summary)
    print()

    # Display ASCII dashboard
    print("7. Live Dashboard:")
    print()
    dashboard = hooks.dashboard_ascii()
    print(dashboard)
    print()

    # Export to JSON
    print("8. JSON Export Sample:")
    print()
    json_export = hooks.export_metrics(format="json")
    # Print first 500 chars
    print(json_export[:500] + "...")
    print()

    # Demonstrate reset
    print("9. Metrics Reset:")
    print(f"   Before reset - Total calls: {hooks.get_call_count()}")
    hooks.reset_metrics()
    print(f"   After reset - Total calls: {hooks.get_call_count()}")
    print()

    print("=" * 70)
    print("Demonstration Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
