# QE Fleet Hooks System - Quick Reference

## Initialization

```python
from lionagi_qe.core.fleet import QEFleet

# Enable hooks with default settings
fleet = QEFleet(enable_hooks=True)

# Customize hooks
fleet = QEFleet(
    enable_hooks=True,
    fleet_id="my-fleet",
    cost_alert_threshold=10.0
)
```

## Core Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `fleet.get_metrics()` | `Dict[str, Any]` | Full metrics with all dimensions |
| `fleet.get_call_count()` | `int` | Total AI calls made |
| `fleet.get_cost_summary()` | `str` | Human-readable cost summary |
| `fleet.get_dashboard()` | `str` | ASCII dashboard view |
| `fleet.export_hooks_metrics()` | `str` | Export in JSON/summary format |
| `fleet.reset_metrics()` | `None` | Reset all counters to zero |

## Quick Examples

### Check Total Cost
```python
metrics = fleet.get_metrics()
print(f"Total: ${metrics['hooks']['total_cost']:.2f}")
```

### Display Dashboard
```python
print(fleet.get_dashboard())
```

### Export to File
```python
with open("metrics.json", "w") as f:
    f.write(fleet.export_hooks_metrics(format="json"))
```

### Reset Between Runs
```python
fleet.reset_metrics()
# Run new batch of tasks
await fleet.execute_pipeline(...)
```

## Metrics Structure

```python
{
    "total_cost": 0.2661,
    "total_calls": 10,
    "by_agent": {
        "test-generator": {"total_cost": 0.009, "call_count": 5},
        "coverage-analyzer": {"total_cost": 0.216, "call_count": 3}
    },
    "by_model": {
        "openai/gpt-3.5-turbo": {"total_cost": 0.009, "call_count": 5}
    },
    "by_provider": {
        "openai": {"total_cost": 0.225, "call_count": 8}
    },
    "token_usage": {
        "total_tokens": 18550,
        "total_input_tokens": 9500,
        "total_output_tokens": 9050
    }
}
```

## Common Patterns

### Monitor Costs in Loop
```python
while processing:
    await fleet.execute(...)
    metrics = fleet.get_metrics()
    if metrics['hooks']['total_cost'] > 50.0:
        send_alert()
```

### Find Expensive Agents
```python
metrics = fleet.get_metrics()
expensive = sorted(
    metrics['hooks']['by_agent'].items(),
    key=lambda x: x[1]['total_cost'],
    reverse=True
)[:5]
```

### Track Cost Trends
```python
history = []
for batch in batches:
    fleet.reset_metrics()
    await process_batch(batch)
    history.append(fleet.get_metrics())
```

## Alert System

```python
# Set threshold
fleet = QEFleet(enable_hooks=True, cost_alert_threshold=5.0)

# Check alerts
metrics = fleet.get_metrics()
if metrics['hooks']['alerts_triggered'] > 0:
    print(f"Cost exceeded ${fleet.hooks.cost_alert_threshold}")
```

## Pricing (per 1M tokens)

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-3.5-turbo | $0.50 | $1.50 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | gpt-4 | $30.00 | $60.00 |
| Anthropic | claude-3-5-sonnet | $3.00 | $15.00 |
| Anthropic | claude-3-haiku | $0.25 | $1.25 |

## Files

- **Core**: `src/lionagi_qe/core/hooks.py`
- **Tests**: `tests/core/test_hooks_integration.py`
- **Demo**: `examples/hooks_demo_standalone.py`
- **Docs**: `docs/HOOKS_SYSTEM_GUIDE.md`

## Status

✅ Production Ready
✅ Zero Configuration
✅ <1ms Overhead
✅ Fully Tested
