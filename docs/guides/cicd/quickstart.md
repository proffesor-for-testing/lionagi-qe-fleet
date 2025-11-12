# 5-Minute CI/CD Quickstart

Get LionAGI QE Fleet running in your CI pipeline in under 5 minutes.

---

## Prerequisites

- Python 3.10 or higher
- CI platform account (GitHub Actions, GitLab CI, Jenkins, etc.)
- Anthropic API key ([get one here](https://console.anthropic.com/))

---

## Step 1: Install (30 seconds)

### Local Testing (Optional)

```bash
pip install lionagi-qe-fleet
```

### In CI (Automated)

Installation is handled automatically in your CI configuration (see Step 3).

---

## Step 2: Get API Key (1 minute)

### Option A: Anthropic API Key (Recommended)

1. Visit https://console.anthropic.com/
2. Create an account or sign in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy your key (starts with `sk-ant-...`)

### Option B: OpenAI API Key

1. Visit https://platform.openai.com/
2. Create API key
3. Copy your key (starts with `sk-...`)

**Add to CI Secrets:**
- GitHub Actions: Settings → Secrets → Actions → "New repository secret"
- GitLab CI: Settings → CI/CD → Variables → "Add variable"
- Jenkins: Credentials → System → Global credentials → "Add credentials"

---

## Step 3: Add to CI Configuration (2 minutes)

Choose your platform:

### GitHub Actions

Create `.github/workflows/qe-fleet.yml`:

```yaml
name: QE Fleet

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-engineering:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install QE Fleet
        run: pip install lionagi-qe-fleet

      - name: Generate Tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          aqe generate src/ --ci-mode --json --output tests/generated/

      - name: Run Tests
        run: |
          aqe execute tests/ --parallel --coverage --format json

      - name: Quality Gate
        run: |
          aqe quality-gate --coverage-threshold 80 --fail-on-error
```

### GitLab CI

Create or update `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - quality

qe_generate_tests:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install lionagi-qe-fleet
  script:
    - aqe generate src/ --ci-mode --json --output tests/generated/
    - aqe execute tests/ --parallel --coverage
  coverage: '/Coverage: (\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - tests/generated/
      - coverage.xml
    expire_in: 30 days

qe_quality_gate:
  stage: quality
  image: python:3.11-slim
  before_script:
    - pip install lionagi-qe-fleet
  script:
    - aqe quality-gate --coverage-threshold 80 --fail-on-error
  needs:
    - qe_generate_tests
```

### Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install lionagi-qe-fleet'
            }
        }

        stage('Generate Tests') {
            steps {
                sh '''
                    aqe generate src/ --ci-mode --json --output tests/generated/
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    aqe execute tests/ --parallel --coverage
                '''
            }
        }

        stage('Quality Gate') {
            steps {
                sh '''
                    aqe quality-gate --coverage-threshold 80 --fail-on-error
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml,tests/generated/**', allowEmptyArchive: true
            publishHTML([
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

### CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  qe-tests:
    docker:
      - image: python:3.11

    steps:
      - checkout

      - run:
          name: Install QE Fleet
          command: pip install lionagi-qe-fleet

      - run:
          name: Generate Tests
          command: |
            aqe generate src/ --ci-mode --json --output tests/generated/

      - run:
          name: Run Tests
          command: |
            aqe execute tests/ --parallel --coverage

      - run:
          name: Quality Gate
          command: |
            aqe quality-gate --coverage-threshold 80 --fail-on-error

      - store_artifacts:
          path: coverage.xml
          destination: coverage

      - store_artifacts:
          path: tests/generated
          destination: generated-tests

workflows:
  qe-pipeline:
    jobs:
      - qe-tests
```

---

## Step 4: Verify (1 minute)

### Commit and Push

```bash
git add .github/workflows/qe-fleet.yml  # or your CI config
git commit -m "Add QE Fleet integration"
git push
```

### Check CI Logs

Your CI should now run QE Fleet. Check the logs for:

✅ **Successful installation** - "Successfully installed lionagi-qe-fleet"
✅ **Test generation** - "Generated X tests for Y files"
✅ **Test execution** - "X tests passed, Y failed"
✅ **Quality gate** - "Quality gate: PASSED" or "Quality gate: FAILED"

---

## What Just Happened?

1. **QE Fleet Installed** - Installed from PyPI in your CI environment
2. **Tests Generated** - AI analyzed your code and generated comprehensive tests
3. **Tests Executed** - Tests ran in parallel with coverage tracking
4. **Quality Gate** - Automated quality validation against your thresholds

---

## Next Steps

### Add More Capabilities

**Security Scanning**:
```yaml
- name: Security Scan
  run: aqe security-scan src/ --comprehensive
```

**Performance Testing**:
```yaml
- name: Performance Test
  run: aqe performance-test tests/perf/ --load 100
```

**Badge Generation** (README.md):
```markdown
![Coverage](https://api.example.com/badge/coverage/org/repo)
![Quality](https://api.example.com/badge/quality/org/repo)
```

### Learn More

- [CLI Usage Guide](./cli-ci.md) - All CLI flags and options
- [Webhook API](./webhook-integration.md) - Advanced integrations
- [Artifact Storage](./artifact-storage.md) - Store historical results
- [Best Practices](./best-practices.md) - Recommended patterns
- [Example Workflows](./examples/) - More complete examples

---

## Common Issues

### "ImportError: No module named lionagi_qe"

**Solution**: Ensure `pip install lionagi-qe-fleet` ran successfully. Check pip version (requires pip 20+).

### "API key not found"

**Solution**: Check that your API key is properly set as a CI secret and correctly referenced in the environment variable.

### "Tests failed: Coverage below threshold"

**Solution**: This is expected behavior. Either:
- Improve test coverage to meet the threshold
- Lower the threshold temporarily: `--coverage-threshold 60`
- Remove quality gate until coverage improves

### "Command 'aqe' not found"

**Solution**:
- Ensure installation step completed successfully
- Check Python path is in $PATH
- Try using `python -m lionagi_qe` instead of `aqe`

[→ Full Troubleshooting Guide](./troubleshooting.md)

---

## Success! 🎉

You now have AI-powered quality engineering running in your CI pipeline!

### What's Next?

1. Review generated tests in `tests/generated/`
2. Commit the tests to your repository
3. Configure quality gates to your standards
4. Add badges to your README
5. Set up artifact storage for historical tracking

**Need Help?**
- [Documentation](./index.md)
- [GitHub Issues](https://github.com/lionagi/lionagi-qe-fleet/issues)
- [GitHub Discussions](https://github.com/lionagi/lionagi-qe-fleet/discussions)

---

**Total Time**: ⏱️ 5 minutes
**Difficulty**: 🟢 Beginner
**Last Updated**: 2025-11-12
