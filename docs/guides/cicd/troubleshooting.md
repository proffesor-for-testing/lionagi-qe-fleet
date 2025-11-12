# CI/CD Integration Troubleshooting

**Common issues and solutions for QE Fleet CI/CD integration**

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Authentication Errors](#authentication-errors)
3. [CLI Command Errors](#cli-command-errors)
4. [API Errors](#api-errors)
5. [Storage Configuration](#storage-configuration)
6. [Badge Rendering](#badge-rendering)
7. [Performance Issues](#performance-issues)
8. [Debug Mode](#debug-mode)

---

## Installation Issues

### "Module not found: lionagi_qe"

**Symptoms**:
```
ImportError: No module named 'lionagi_qe'
ModuleNotFoundError: No module named 'lionagi_qe'
```

**Solutions**:

1. **Verify installation**:
```bash
pip show lionagi-qe-fleet
pip list | grep lionagi
```

2. **Reinstall**:
```bash
pip uninstall lionagi-qe-fleet
pip install lionagi-qe-fleet==1.2.1
```

3. **Check Python version**:
```bash
python --version  # Must be 3.10+
```

4. **Use full module path in CI**:
```bash
python -m lionagi_qe.cli generate src/
```

---

### "Command 'aqe' not found"

**Symptoms**:
```
bash: aqe: command not found
```

**Solutions**:

1. **Check PATH**:
```bash
which aqe
echo $PATH
pip show -f lionagi-qe-fleet | grep aqe
```

2. **Use full path**:
```bash
~/.local/bin/aqe generate src/
# or
python -m lionagi_qe.cli generate src/
```

3. **Add to PATH in CI**:
```bash
export PATH="$HOME/.local/bin:$PATH"
aqe generate src/
```

---

### "pip: No matching distribution found"

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement lionagi-qe-fleet
```

**Solutions**:

1. **Update pip**:
```bash
pip install --upgrade pip
```

2. **Check network/proxy**:
```bash
pip install --verbose lionagi-qe-fleet
```

3. **Use specific Python version**:
```bash
python3.11 -m pip install lionagi-qe-fleet
```

---

## Authentication Errors

### "API key not found"

**Symptoms**:
```
Error: ANTHROPIC_API_KEY environment variable not set
AuthenticationError: No API key found
```

**Solutions**:

1. **Check environment variable**:
```bash
echo $ANTHROPIC_API_KEY  # Should show key
env | grep ANTHROPIC     # List all ANTHROPIC vars
```

2. **Set in CI secrets** (platform-specific):

**GitHub Actions**:
```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**GitLab CI**:
```yaml
variables:
  ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY  # Set in CI/CD settings
```

**Jenkins**:
```groovy
environment {
    ANTHROPIC_API_KEY = credentials('anthropic-api-key')
}
```

3. **Verify key format**:
```bash
# Should start with sk-ant-
echo $ANTHROPIC_API_KEY | cut -c1-7
# Output: sk-ant-
```

---

### "Invalid API key"

**Symptoms**:
```
AuthenticationError: Invalid API key
401 Unauthorized
```

**Solutions**:

1. **Regenerate API key** at https://console.anthropic.com/
2. **Update CI secret** with new key
3. **Check for extra spaces/newlines**:
```bash
export ANTHROPIC_API_KEY=$(echo "$ANTHROPIC_API_KEY" | tr -d '[:space:]')
```

---

### "Rate limit exceeded"

**Symptoms**:
```
RateLimitError: Rate limit exceeded
429 Too Many Requests
```

**Solutions**:

1. **Wait and retry**:
```bash
for i in {1..3}; do
  aqe generate src/ && break
  sleep 60
done
```

2. **Reduce parallel execution**:
```bash
aqe generate src/ --parallel false
```

3. **Enable multi-model routing** (uses cheaper models):
```bash
export QE_ROUTING_ENABLED=true
aqe generate src/
```

---

## CLI Command Errors

### "Tests failed: Coverage below threshold"

**Symptoms**:
```
Quality gate failed: Coverage 75.3% below threshold 80%
Exit code: 2
```

**This is expected behavior!** Solutions:

1. **Lower threshold temporarily**:
```bash
aqe quality-gate --coverage-threshold 70
```

2. **Make non-blocking**:
```bash
aqe quality-gate --threshold 80 || echo "⚠️ Quality gate failed (non-blocking)"
```

3. **Improve coverage**:
- Generate more tests: `aqe generate src/ --coverage-target 90`
- Run existing tests: `aqe execute tests/ --coverage`

---

### "Timeout during test generation"

**Symptoms**:
```
TimeoutError: Operation timed out after 300s
```

**Solutions**:

1. **Increase timeout**:
```bash
aqe generate src/ --timeout 600
# or
export QE_GENERATION_TIMEOUT=600
aqe generate src/
```

2. **Generate smaller batches**:
```bash
aqe generate src/module1/
aqe generate src/module2/
```

3. **Use parallel generation**:
```bash
aqe generate src/ --parallel
```

---

### "JSON output is invalid"

**Symptoms**:
```
JSONDecodeError: Expecting value: line 1 column 1
```

**Solutions**:

1. **Ensure `--json` flag is used**:
```bash
aqe generate src/ --json
```

2. **Check for mixed output**:
```bash
aqe generate src/ --json --quiet  # Suppress other output
```

3. **Redirect stderr**:
```bash
aqe generate src/ --json 2>/dev/null
```

---

## API Errors

### "Connection refused"

**Symptoms**:
```
ConnectionError: Connection refused to api.example.com:443
```

**Solutions**:

1. **Check API server is running**:
```bash
curl https://api.example.com/health
```

2. **Check firewall/network**:
```bash
telnet api.example.com 443
ping api.example.com
```

3. **Use correct URL**:
```bash
# Ensure https:// prefix
curl https://api.example.com/api/v1/qe/generate
```

---

### "API returns 500 Internal Server Error"

**Symptoms**:
```
HTTPError: 500 Internal Server Error
```

**Solutions**:

1. **Retry with exponential backoff**:
```bash
for i in {1..5}; do
  curl -X POST https://api.example.com/api/v1/qe/generate \
    -H "Authorization: Bearer $API_KEY" \
    -d '{}' && break
  sleep $((2**i))
done
```

2. **Check API logs** (if self-hosted)
3. **Contact support** with request ID

---

## Storage Configuration

### "S3 bucket not accessible"

**Symptoms**:
```
boto3.exceptions.NoCredentialsError
S3Error: Access Denied
```

**Solutions**:

1. **Check AWS credentials**:
```bash
aws s3 ls s3://my-qe-artifacts/
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

2. **Verify bucket permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::my-qe-artifacts/*"]
  }]
}
```

3. **Check bucket exists**:
```bash
aws s3 mb s3://my-qe-artifacts
```

---

### "Artifact not found"

**Symptoms**:
```
ArtifactNotFoundError: No artifact found for key 'build-abc123'
```

**Solutions**:

1. **List available artifacts**:
```bash
aqe artifacts list --limit 20
```

2. **Check artifact key**:
```bash
# Ensure key matches what was stored
aqe artifacts get build-abc123
```

3. **Verify storage backend**:
```bash
echo $QE_STORAGE_BACKEND
cat config/storage.json
```

---

## Badge Rendering

### "Badge shows 'unknown'"

**Symptoms**:
Badge displays with "unknown" value or gray color.

**Solutions**:

1. **Check artifact data exists**:
```bash
aqe artifacts get --project org/repo --latest
```

2. **Force badge refresh**:
```markdown
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?nocache=1)
```

3. **Verify project name**:
```bash
# Should match artifact storage project ID
curl https://api.example.com/api/v1/badge/coverage/org/repo
```

---

### "Badge not displaying in GitHub"

**Symptoms**:
Badge URL works in browser but not in GitHub README.

**Solutions**:

1. **Use absolute URL**:
```markdown
<!-- ✅ Correct -->
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo)

<!-- ❌ Wrong -->
![Coverage](../badges/coverage.svg)
```

2. **Check CORS headers** (if self-hosted):
```
Access-Control-Allow-Origin: *
```

3. **Use shields.io proxy**:
```markdown
![Coverage](https://img.shields.io/endpoint?url=https://api.example.com/api/v1/badge/coverage/org/repo)
```

---

## Performance Issues

### "CI runs are slow"

**Symptoms**:
QE Fleet operations take >10 minutes in CI.

**Solutions**:

1. **Enable parallel execution**:
```bash
aqe generate src/ --parallel
aqe execute tests/ --parallel
```

2. **Use multi-model routing** (faster cheap models):
```bash
export QE_ROUTING_ENABLED=true
```

3. **Generate incrementally**:
```bash
# Only generate for changed files
git diff --name-only HEAD^ | grep '\.py$' | xargs aqe generate
```

4. **Cache dependencies**:
```yaml
# GitHub Actions
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

---

### "High AI API costs"

**Symptoms**:
Monthly AI API costs are unexpectedly high.

**Solutions**:

1. **Enable cost optimization**:
```bash
export QE_ROUTING_ENABLED=true  # 70-80% savings
```

2. **Monitor usage**:
```bash
aqe usage report --since 2025-11-01
```

3. **Set cost limits**:
```python
# config/routing.json
{
  "cost_limits": {
    "daily": 10.00,
    "monthly": 200.00
  }
}
```

---

## Debug Mode

### Enable Debug Logging

```bash
# Set log level
export QE_LOG_LEVEL=DEBUG

# Log to file
export QE_LOG_FILE=/tmp/qe-fleet-debug.log

# Run command
aqe generate src/ --ci-mode

# Check logs
tail -f /tmp/qe-fleet-debug.log
```

### Verbose Output

```bash
# CLI verbose mode
aqe generate src/ --verbose

# API debug mode
curl -X POST https://api.example.com/api/v1/qe/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "X-Debug: true" \
  -d '{...}'
```

### Health Check

```bash
# Check QE Fleet installation
aqe --version
aqe health-check

# Check API
curl https://api.example.com/health
```

---

## Getting Help

### 1. Search Documentation
- [Overview](./overview.md)
- [CLI Usage](./cli-ci.md)
- [Webhook API](./webhook-integration.md)
- [FAQ](./faq.md)

### 2. Check GitHub Issues
- [Existing Issues](https://github.com/lionagi/lionagi-qe-fleet/issues)
- [Search Issues](https://github.com/lionagi/lionagi-qe-fleet/issues?q=)

### 3. Ask Community
- [GitHub Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions)

### 4. File Bug Report
- [New Issue](https://github.com/lionagi/lionagi-qe-fleet/issues/new?template=bug_report.md)

**Include**:
- QE Fleet version: `aqe --version`
- Python version: `python --version`
- OS: `uname -a`
- Error message (full traceback)
- Steps to reproduce
- Debug logs

---

**Last Updated**: 2025-11-12
