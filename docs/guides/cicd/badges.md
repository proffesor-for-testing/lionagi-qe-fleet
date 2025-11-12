# Badge Integration Guide

**Display coverage, quality, security, and test metrics in your README**

---

## Overview

QE Fleet provides shields.io-compatible SVG badges for displaying metrics.

**Available Badges**:
- Coverage (percentage)
- Quality Score (0-100)
- Security Grade (A+ to F)
- Test Count (passing/total)
- Build Status

---

## Quick Start

### 1. Generate Badge

```bash
# Via CLI
aqe badge generate coverage --project org/repo --output badge.svg

# Via API
curl https://api.example.com/api/v1/badge/coverage/org/repo > badge.svg
```

### 2. Add to README

```markdown
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo)
![Quality](https://api.example.com/api/v1/badge/quality/org/repo)
![Security](https://api.example.com/api/v1/badge/security/org/repo)
![Tests](https://api.example.com/api/v1/badge/tests/org/repo)
```

---

## Badge Types

### Coverage Badge

Shows test coverage percentage with color coding.

**URL**:
```
https://api.example.com/api/v1/badge/coverage/{org}/{repo}
```

**Color Coding**:
- 🔴 Red (<60%) - Needs improvement
- 🟡 Yellow (60-80%) - Acceptable
- 🟢 Green (>80%) - Excellent

**Example**:
![Coverage](https://img.shields.io/badge/coverage-87.5%25-brightgreen)

---

### Quality Badge

Shows overall quality score (0-100).

**URL**:
```
https://api.example.com/api/v1/badge/quality/{org}/{repo}
```

**Color Coding**:
- 🔴 Red (<70) - Poor quality
- 🟡 Yellow (70-85) - Acceptable
- 🟢 Green (>85) - Excellent

**Example**:
![Quality](https://img.shields.io/badge/quality-92-brightgreen)

---

### Security Badge

Shows security grade (A+ to F).

**URL**:
```
https://api.example.com/api/v1/badge/security/{org}/{repo}
```

**Grades**:
- 🟢 A+, A (Excellent)
- 🟡 B+, B (Good)
- 🟠 C+, C (Acceptable)
- 🔴 D, F (Poor)

**Example**:
![Security](https://img.shields.io/badge/security-A+-brightgreen)

---

### Test Count Badge

Shows passing/total test count.

**URL**:
```
https://api.example.com/api/v1/badge/tests/{org}/{repo}
```

**Format**: `passing/total`

**Example**:
![Tests](https://img.shields.io/badge/tests-154%2F156-green)

---

## Customization

### Style

Add `?style=` parameter:

```markdown
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?style=flat)
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?style=flat-square)
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?style=plastic)
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?style=for-the-badge)
```

### Custom Color

Add `?color=` parameter:

```markdown
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?color=blue)
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?color=ff69b4)
```

### Custom Label

Add `?label=` parameter:

```markdown
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?label=test%20coverage)
```

---

## Caching

Badges are cached for performance:

- **Default TTL**: 300 seconds (5 minutes)
- **Cache-Control**: `public, max-age=300`
- **Force Refresh**: Add `?nocache=1`

```markdown
<!-- Always fresh (not recommended) -->
![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?nocache=1)
```

---

## Badge API Endpoints

### Generate Coverage Badge

**GET** `/api/v1/badge/coverage/{org}/{repo}`

**Query Parameters**:
- `style` - Badge style (flat, flat-square, plastic, for-the-badge)
- `color` - Custom color (hex or name)
- `label` - Custom label text

**Response**: SVG image (`image/svg+xml`)

---

### Generate Quality Badge

**GET** `/api/v1/badge/quality/{org}/{repo}`

Same parameters as coverage badge.

---

### Generate Security Badge

**GET** `/api/v1/badge/security/{org}/{repo}`

Same parameters as coverage badge.

---

### Generate Test Count Badge

**GET** `/api/v1/badge/tests/{org}/{repo}`

Same parameters as coverage badge.

---

## CI Integration

### Update Badges After CI Run

**GitHub Actions**:
```yaml
- name: Update Badges
  if: github.ref == 'refs/heads/main'
  run: |
    curl -X POST https://api.example.com/api/v1/badge/refresh \
      -H "Authorization: Bearer ${{ secrets.QE_API_KEY }}" \
      -d '{"project": "${{ github.repository }}"}'
```

**GitLab CI**:
```yaml
update_badges:
  stage: deploy
  only:
    - main
  script:
    - |
      curl -X POST https://api.example.com/api/v1/badge/refresh \
        -H "Authorization: Bearer $QE_API_KEY" \
        -d '{"project": "$CI_PROJECT_PATH"}'
```

---

## Complete README Example

```markdown
# My Awesome Project

![Coverage](https://api.example.com/api/v1/badge/coverage/org/repo?style=flat-square)
![Quality](https://api.example.com/api/v1/badge/quality/org/repo?style=flat-square)
![Security](https://api.example.com/api/v1/badge/security/org/repo?style=flat-square)
![Tests](https://api.example.com/api/v1/badge/tests/org/repo?style=flat-square)
![Build](https://github.com/org/repo/workflows/CI/badge.svg)

Comprehensive description of your project...

## Quality Metrics

- **Test Coverage**: 87.5% (auto-generated by QE Fleet)
- **Code Quality**: 92/100
- **Security Grade**: A+
- **Tests Passing**: 154/156

## Testing

Tests are automatically generated and executed using [LionAGI QE Fleet](https://github.com/lionagi/lionagi-qe-fleet).

\```bash
# Run tests
pytest tests/

# Generate new tests
aqe generate src/
\```
```

---

## Troubleshooting

### Badge Not Displaying

**Check**:
1. URL is correct
2. Project exists in artifact storage
3. API is accessible
4. No network/firewall blocking

### Badge Shows Wrong Value

**Solutions**:
- Force refresh: Add `?nocache=1`
- Check artifact storage has latest data
- Verify CI is updating artifacts

### Badge Shows "unknown"

**Causes**:
- No artifact data for project
- Project name incorrect
- API authentication failed

[→ Full Troubleshooting Guide](./troubleshooting.md)

---

## Best Practices

1. **Use flat-square style** - Modern, clean
2. **Place badges at top of README** - High visibility
3. **Link badges to detailed reports** - Provide context
4. **Update on main branch only** - Stable metrics
5. **Cache badges appropriately** - Balance freshness/performance
6. **Use consistent style** - Professional appearance

---

## Next Steps

- [Artifact Storage](./artifact-storage.md) - Store badge data
- [Webhook API](./webhook-integration.md) - Update badges programmatically
- [Troubleshooting](./troubleshooting.md) - Badge issues

---

**Last Updated**: 2025-11-12
