# User Guides

Practical guides for using the LionAGI QE Fleet effectively.

## Available Guides

### Getting Started
- [Migration Guide](migration.md) - Migrate from other testing frameworks
- [Advanced Features Migration](advanced-features-migration.md) - Adopt advanced features

### CI/CD Integration (NEW)
- [CI/CD Integration Plan](cicd-integration-goap-plan.md) - Complete 60+ page roadmap
- [CI/CD Executive Summary](cicd-integration-executive-summary.md) - 10-minute overview
- [CI/CD Visual Roadmap](cicd-roadmap-visual.md) - Timeline and dependency graph
- [CI/CD Quick Reference](cicd-quick-reference.md) - One-page cheat sheet

### Best Practices
- [Agent Coordination](agent-coordination.md) - Coordinate agents effectively
- [Multi-Agent Patterns](multi-agent-patterns.md) - Advanced multi-agent workflows
- [Cost Optimization](cost-optimization.md) - Save 70-81% on AI costs
- [Observability](observability.md) - Monitor fleet operations

## Quick Links

| Guide | Purpose | Audience |
|-------|---------|----------|
| [Migration Guide](migration.md) | Switch from other frameworks | Teams adopting QE Fleet |
| [Agent Coordination](agent-coordination.md) | Coordinate multiple agents | All users |
| [Cost Optimization](cost-optimization.md) | Reduce AI costs | Budget-conscious teams |
| [Observability](observability.md) | Monitor and debug | DevOps, SRE teams |

## Guide Summaries

### Migration Guide

**Who**: Teams switching from Jest, pytest, Selenium, or other frameworks

**What**: Step-by-step migration instructions with examples

**Key Topics**:
- Mapping existing tests to agents
- Converting test suites
- Integrating with CI/CD
- Preserving coverage

**Start Here**: [Migration Guide](migration.md)

---

### Agent Coordination

**Who**: All QE Fleet users

**What**: Best practices for coordinating multiple agents

**Key Topics**:
- Memory namespace (`aqe/*`)
- Agent communication patterns
- Shared context
- Result passing between agents

**Example**:
```python
# Agent 1 stores results
await fleet.memory.store("aqe/test-gen/results", test_results)

# Agent 2 retrieves and builds on it
prev_results = await fleet.memory.retrieve("aqe/test-gen/results")
coverage = await analyze_coverage(prev_results)
```

**Start Here**: [Agent Coordination](agent-coordination.md)

---

### Cost Optimization

**Who**: Budget-conscious teams, high-volume users

**What**: Strategies to minimize AI API costs

**Key Topics**:
- Multi-model routing (up to 80% theoretical savings)
- Model selection strategies
- Cost monitoring and tracking
- Usage optimization

**Example Savings**:
```
Before routing: 100 tasks × $0.0048 (GPT-4) = $0.48
After routing:
  - 70 simple → GPT-3.5: $0.028
  - 25 moderate → GPT-4o-mini: $0.020
  - 5 complex → GPT-4: $0.024
Total: $0.072 (85% savings!)
```

**Start Here**: [Cost Optimization](cost-optimization.md)

---

### Observability

**Who**: DevOps, SRE teams, debugging users

**What**: Monitor fleet operations and troubleshoot issues

**Key Topics**:
- Fleet status monitoring
- Cost tracking
- Agent metrics
- Debugging workflows
- Log analysis

**Example**:
```python
status = await fleet.get_status()
print(f"Workflows: {status['orchestration_metrics']['workflows_executed']}")
print(f"Cost: ${status['routing_stats']['total_cost']:.4f}")
print(f"Agents: {status['orchestration_metrics']['total_agents_used']}")
```

**Start Here**: [Observability](observability.md)

---

### Multi-Agent Patterns

**Who**: Advanced users, architects

**What**: Complex multi-agent coordination patterns

**Key Topics**:
- Hierarchical coordination
- Dynamic agent selection
- Workflow composition
- Error handling and retries

**Example**:
```python
# Hierarchical: Fleet commander coordinates specialists
result = await fleet.execute_fan_out_fan_in(
    coordinator="fleet-commander",
    workers=["test-gen", "security", "performance"],
    context={"request": "Comprehensive QA"}
)
```

**Start Here**: [Multi-Agent Patterns](multi-agent-patterns.md)

## Common Use Cases

### Use Case 1: Migrating from pytest

**Goal**: Replace manual pytest writing with AI-powered generation

**Steps**:
1. Install QE Fleet: `pip install lionagi-qe-fleet`
2. Initialize fleet with routing
3. Use TestGeneratorAgent for test generation
4. Use TestExecutorAgent to run generated tests
5. Compare coverage with original suite

**Guide**: [Migration Guide](migration.md)

---

### Use Case 2: CI/CD Integration

**Goal**: Integrate QE Fleet into CI/CD pipeline

**Steps**:
1. Set up API keys in CI environment
2. Create fleet initialization script
3. Define sequential pipeline (generate → execute → gate)
4. Export results for CI reporting
5. Fail build on quality gate rejection

**Guide**: [Agent Coordination](agent-coordination.md)

---

### Use Case 3: Cost Reduction

**Goal**: Reduce AI API costs by 70%+

**Steps**:
1. Enable multi-model routing
2. Monitor routing statistics
3. Adjust complexity thresholds
4. Cache expensive operations
5. Track savings over time

**Guide**: [Cost Optimization](cost-optimization.md)

---

### Use Case 4: Debugging Failures

**Goal**: Understand why agent failed or produced unexpected results

**Steps**:
1. Check agent metrics
2. Review fleet status
3. Examine memory namespace
4. Analyze logs
5. Replay with verbose logging

**Guide**: [Observability](observability.md)

## Best Practices Checklist

### Before Production
- [ ] Enable routing for cost savings
- [ ] Set up monitoring and alerts
- [ ] Configure memory TTLs
- [ ] Test error handling
- [ ] Document agent workflows
- [ ] Set up CI/CD integration

### During Development
- [ ] Use memory namespace for coordination
- [ ] Parallelize independent agents
- [ ] Monitor costs regularly
- [ ] Track agent metrics
- [ ] Log important operations

### After Deployment
- [ ] Monitor fleet status
- [ ] Review cost reports
- [ ] Analyze agent performance
- [ ] Optimize slow workflows
- [ ] Update routing configuration

## Troubleshooting Guide

### Problem: Agent not producing expected results

**Check**:
1. Agent configuration (model, system prompt)
2. Task context (all required fields?)
3. Memory namespace (correct keys?)
4. Agent logs (errors or warnings?)

**Solution**: [Observability Guide](observability.md)

---

### Problem: High costs

**Check**:
1. Is routing enabled?
2. Are tasks classified correctly?
3. Is caching utilized?
4. Are there unnecessary API calls?

**Solution**: [Cost Optimization Guide](cost-optimization.md)

---

### Problem: Slow execution

**Check**:
1. Are agents running in parallel?
2. Is there unnecessary sequencing?
3. Are there rate limits?
4. Is memory retrieval optimized?

**Solution**: [Agent Coordination Guide](agent-coordination.md)

---

### Problem: Agent coordination failures

**Check**:
1. Memory namespace keys correct?
2. Are TTLs expiring too soon?
3. Is agent execution order correct?
4. Are dependencies handled?

**Solution**: [Multi-Agent Patterns Guide](multi-agent-patterns.md)

## Next Steps

Choose your path:

**New Users**:
1. [Migration Guide](migration.md) - Get started
2. [Agent Coordination](agent-coordination.md) - Learn basics
3. [Observability](observability.md) - Monitor operations

**Advanced Users**:
1. [Multi-Agent Patterns](multi-agent-patterns.md) - Complex workflows
2. [Cost Optimization](cost-optimization.md) - Maximize efficiency
3. [Advanced Topics](../advanced/index.md) - Deep dives

**Operators**:
1. [Observability](observability.md) - Monitor fleet
2. [Cost Optimization](cost-optimization.md) - Control costs
3. [Troubleshooting](#troubleshooting-guide) - Debug issues

---

**See Also**: [Workflow Patterns](../patterns/index.md) | [Agent Catalog](../agents/index.md) | [Architecture](../architecture/system-overview.md)
