# CI/CD Integration FAQ

**Frequently Asked Questions**

---

## General Questions

### What is LionAGI QE Fleet?

LionAGI QE Fleet is an **autonomous quality engineering framework** powered by 19 specialized AI agents. It automates test generation, execution, coverage analysis, security scanning, and quality gates in your CI/CD pipeline.

**Key Features**:
- AI-powered test generation
- 19 specialized QE agents
- Multi-model cost optimization (70-80% savings)
- Framework-agnostic (pytest, Jest, Mocha, etc.)
- Open source (MIT license)

[→ Overview](./overview.md)

---

### How does it compare to GitHub Copilot or traditional testing tools?

| Feature | QE Fleet | GitHub Copilot | Codecov | SonarQube |
|---------|----------|----------------|---------|-----------|
| **AI Test Generation** | ✅ 19 specialized agents | ⚠️ 1 general agent | ❌ No | ❌ No |
| **Coverage Analysis** | ✅ Real-time | ❌ No | ✅ Yes | ✅ Yes |
| **Security Scanning** | ✅ Comprehensive | ❌ No | ❌ No | ✅ Yes |
| **Performance Testing** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Cost** | ⚠️ AI API costs | $10-20/month | $29+/month | $150+/month |
| **Open Source** | ✅ MIT | ❌ No | ❌ No | ⚠️ Limited |

**Bottom Line**: QE Fleet is **more comprehensive** than Copilot, **more cost-effective** than traditional tools (with multi-model routing), and **fully open source**.

---

### Does QE Fleet replace my existing tests?

**No**. QE Fleet **complements** your existing tests:

1. **Generates new tests** for uncovered code
2. **Identifies gaps** in existing test suites
3. **Runs alongside** your existing tests
4. **Integrates with** existing frameworks (pytest, Jest, etc.)

**Best Practice**: Keep your existing tests and use QE Fleet to:
- Generate tests for new code
- Fill coverage gaps
- Find edge cases you missed

---

## Installation & Setup

### What are the prerequisites?

**Required**:
- Python 3.10 or higher
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Anthropic or OpenAI API key

**Optional**:
- AWS S3 for artifact storage
- PostgreSQL for persistence
- Redis for caching

[→ Quickstart](./quickstart.md)

---

### How long does setup take?

**5 minutes** for basic CI integration:
1. Install: `pip install lionagi-qe-fleet` (30 seconds)
2. Add API key to CI secrets (1 minute)
3. Add CI configuration (2 minutes)
4. Commit and push (30 seconds)
5. Verify first run (1 minute)

[→ 5-Minute Quickstart](./quickstart.md)

---

### Which AI provider should I use?

**Anthropic (Recommended)**:
- ✅ Longer context windows
- ✅ Better reasoning for complex tests
- ✅ More accurate edge case detection
- ⚠️ Slightly higher cost

**OpenAI**:
- ✅ Faster response times
- ✅ Lower cost with GPT-3.5
- ✅ Good for simple tests
- ⚠️ Shorter context windows

**Best Practice**: Use Anthropic for critical code, OpenAI for simple code. Enable multi-model routing for automatic selection (70-80% cost savings).

---

## Usage & Configuration

### How do I configure quality gate thresholds?

```bash
# Via CLI flags
aqe quality-gate --coverage-threshold 80 --quality-threshold 85

# Via config file
# config/quality-gates.json
{
  "coverage": {
    "threshold": 80,
    "fail_on_violation": true
  },
  "quality": {
    "threshold": 85,
    "fail_on_violation": true
  },
  "security": {
    "max_high": 0,
    "max_medium": 3
  }
}

# Use config
aqe quality-gate --config config/quality-gates.json
```

[→ CLI Usage Guide](./cli-ci.md#4-quality-gate)

---

### Can I use QE Fleet with monorepos?

**Yes!** QE Fleet works well with monorepos:

```bash
# Generate tests for specific package
aqe generate packages/api/src/ --output packages/api/tests/

# Run tests for all packages
for pkg in packages/*/; do
  aqe execute "$pkg/tests/" --parallel
done

# Quality gate per package
aqe quality-gate --coverage-threshold 80 --scope packages/api/
```

---

### How do I handle different test frameworks in one project?

```bash
# Python backend (pytest)
aqe generate backend/src/ --framework pytest --output backend/tests/

# JavaScript frontend (Jest)
aqe generate frontend/src/ --framework jest --output frontend/__tests__/

# Run all tests
aqe execute backend/tests/ --framework pytest
aqe execute frontend/__tests__/ --framework jest
```

---

### Can I customize the generated tests?

**Yes, several ways**:

1. **Edit generated tests manually** (recommended):
```bash
aqe generate src/ --output tests/generated/
# Edit tests/generated/*.py
git add tests/generated/
```

2. **Provide test templates**:
```bash
aqe generate src/ --template custom-test-template.j2
```

3. **Configure generation rules**:
```python
# config/generation.json
{
  "style": "london",  # London vs Chicago TDD
  "mock_strategy": "auto",
  "assertion_style": "pytest",
  "edge_cases": true
}
```

---

## Performance & Costs

### How much does it cost?

**AI API Costs** (varies by usage):

**Without Multi-Model Routing**:
- GPT-4: $0.03/1k tokens input, $0.06/1k tokens output
- Typical test generation: ~2k tokens = $0.18 per file
- 100 files = **$18 per run**

**With Multi-Model Routing (Recommended)**:
- Simple files → GPT-3.5: $0.0004 per file
- Complex files → GPT-4: $0.18 per file
- 70% simple, 30% complex = **$5.50 per run** (70% savings!)

**Infrastructure Costs** (optional):
- S3 storage: $0.023/GB/month (~$1/month)
- PostgreSQL: Free (self-hosted) or $15/month (managed)
- API server: Free (self-hosted) or $5-20/month (cloud)

**Total Monthly Cost** (typical team):
- Small team (50 runs/month): $25-$100/month
- Medium team (200 runs/month): $100-$500/month
- Large team (1000 runs/month): $500-$2000/month

**Cost Optimization Tips**:
1. Enable multi-model routing (70-80% savings)
2. Cache generated tests (avoid regeneration)
3. Generate incrementally (only changed files)
4. Use GPT-3.5 for simple code

---

### How long do CI runs take?

**Typical Times**:

| Operation | Without QE Fleet | With QE Fleet (Serial) | With QE Fleet (Parallel) |
|-----------|-----------------|----------------------|------------------------|
| **Test Generation** | Manual (hours) | 2-5 min | 30-60 sec |
| **Test Execution** | 2-5 min | Same | Same |
| **Coverage Analysis** | 10-30 sec | Same | Same |
| **Security Scan** | 1-3 min | Same | Same |
| **Total** | Hours (manual) | 5-10 min | **2-4 min** |

**Speed Optimization Tips**:
1. Enable parallel execution: `--parallel`
2. Use multi-model routing (faster models for simple code)
3. Generate incrementally (only changed files)
4. Cache dependencies

---

### Does QE Fleet slow down my CI pipeline?

**No, it actually speeds up overall development**:

**CI Time**: +2-4 minutes per run
**Developer Time Saved**: -2-3 hours per week (manual testing)
**ROI**: ~95% time savings overall

**Without QE Fleet**:
- CI: 5 min
- Manual test writing: 2 hours
- Manual testing: 1 hour
- **Total**: ~3 hours

**With QE Fleet**:
- CI: 9 min (includes QE Fleet)
- Manual test review: 15 min
- **Total**: ~25 minutes (93% reduction!)

---

## Integration

### Which CI platforms are supported?

**All major platforms**:
- ✅ GitHub Actions
- ✅ GitLab CI
- ✅ Jenkins
- ✅ CircleCI
- ✅ Azure Pipelines
- ✅ Buildkite
- ✅ Travis CI
- ✅ TeamCity
- ✅ Any platform with CLI support

[→ Example Workflows](./examples/)

---

### Can I use QE Fleet with self-hosted CI?

**Yes!** QE Fleet works with:
- Self-hosted GitHub Actions runners
- Self-hosted GitLab runners
- Jenkins on-premise
- Any self-hosted CI with Python support

**No data leaves your infrastructure** (except AI API calls).

---

### Does QE Fleet work with GitHub Enterprise?

**Yes!** QE Fleet is compatible with:
- GitHub Enterprise Server
- GitHub Enterprise Cloud
- GitLab Enterprise Edition
- Jenkins Enterprise

[→ Enterprise Guide](https://github.com/lionagi/lionagi-qe-fleet/discussions)

---

## Security & Privacy

### Is my code sent to external services?

**Only to configured AI providers** (Anthropic or OpenAI):
- Code snippets sent to AI API for test generation
- No storage on AI provider servers
- No training on your code (per provider policies)

**Never sent**:
- Database credentials
- API keys
- Secrets
- PII/sensitive data

**Best Practice**: Use self-hosted LLMs for sensitive code (LionAGI supports local models).

---

### How do I prevent secrets from being in tests?

**Automatic Secret Detection**:
QE Fleet scans generated tests for:
- API keys
- Passwords
- Tokens
- Connection strings

**Manual Review**: Always review generated tests before committing.

**Pre-commit Hooks**:
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  hooks:
    - id: detect-secrets
```

---

### Is QE Fleet SOC 2 compliant?

**In Progress**:
- SOC 2 Type II: In progress
- ISO 27001: Planned
- HIPAA: Contact for guidance

**Current Security**:
- Security score: 95/100
- Vulnerability scanning: Daily
- Dependency updates: Automated
- Input validation: All inputs sanitized
- Secure subprocess execution

[→ Security Policy](../../../SECURITY.md)

---

## Troubleshooting

### Tests are failing in CI but passing locally

**Common Causes**:

1. **Environment differences**:
```bash
# Ensure same dependencies
pip freeze > requirements.txt  # Locally
pip install -r requirements.txt  # In CI
```

2. **Timezone issues**:
```bash
# Set timezone in CI
export TZ=UTC
```

3. **Parallel execution**:
```bash
# Disable parallelism if tests have race conditions
aqe execute tests/ --parallel false
```

[→ Full Troubleshooting Guide](./troubleshooting.md)

---

### "Quality gate failed" but coverage looks good

**Check**:
1. Coverage threshold includes **branch coverage** (not just line coverage)
2. Multiple quality metrics (coverage, quality score, security)
3. Specific files/directories excluded

**Solution**:
```bash
# See detailed failure reason
aqe quality-gate --coverage-threshold 80 --verbose

# Check actual metrics
aqe coverage-analyze --show-gaps
```

---

## Advanced Features

### Can I train QE Fleet on my test patterns?

**Yes!** QE Fleet includes Q-learning for pattern recognition:

```bash
# Enable learning
export QE_LEARNING_ENABLED=true

# QE Fleet automatically learns from:
# - Your existing tests
# - Code patterns
# - Test success/failure
# - Historical data

# View learned patterns
aqe learn status
aqe patterns list
```

[→ Q-Learning Integration](../../Q_LEARNING_INTEGRATION.md)

---

### Can I run QE Fleet offline?

**Partially**:
- ❌ Test generation requires AI API (Anthropic/OpenAI)
- ✅ Test execution works offline
- ✅ Coverage analysis works offline
- ✅ Security scanning works offline (SAST only)

**Workaround**: Use self-hosted LLM with LionAGI (advanced).

---

### Does QE Fleet support custom agents?

**Yes!** Create custom agents:

```python
from lionagi_qe.agents import BaseAgent

class CustomTestAgent(BaseAgent):
    agent_type = "custom-tester"

    async def execute(self, task):
        # Your custom logic
        return result

# Register agent
orchestrator.register_agent("custom-tester", CustomTestAgent)
```

[→ Custom Agents Guide](../../advanced/custom-agents.md)

---

## Community & Support

### How do I get help?

1. **Documentation**: [guides/cicd/](./index.md)
2. **GitHub Issues**: [Bug reports](https://github.com/lionagi/lionagi-qe-fleet/issues)
3. **GitHub Discussions**: [Q&A](https://github.com/lionagi/lionagi-qe-fleet/discussions)
4. **Examples**: [Example workflows](./examples/)

---

### How do I contribute?

We welcome contributions!

1. **Report bugs**: [New issue](https://github.com/lionagi/lionagi-qe-fleet/issues/new)
2. **Suggest features**: [New discussion](https://github.com/lionagi/lionagi-qe-fleet/discussions/new)
3. **Submit PRs**: [Contributing guide](../../../CONTRIBUTING.md)
4. **Improve docs**: Docs are in `docs/` directory

---

### Is there a Discord/Slack community?

**Coming soon!** Meanwhile:
- [GitHub Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions)
- [Twitter](https://twitter.com/lionagi) (TBD)

---

## Didn't find your answer?

- [Search GitHub Issues](https://github.com/lionagi/lionagi-qe-fleet/issues?q=)
- [Ask in Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions/new)
- [Check Troubleshooting Guide](./troubleshooting.md)

---

**Last Updated**: 2025-11-12
**Questions**: 30+
**Topics**: Installation, Usage, Costs, Performance, Security, Troubleshooting
