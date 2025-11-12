# Badge Integration Guide

Complete guide for integrating Agentic QE Fleet badges into your project documentation.

## Overview

The badge generation service provides shields.io compatible SVG badges for:
- **Coverage**: Test coverage percentage
- **Quality**: Overall quality score (0-100)
- **Security**: Security grade or vulnerability counts
- **Tests**: Total passing test count

## Quick Start

### Markdown Integration

Add badges to your `README.md`:

```markdown
![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet)
![Quality](https://api.lionagi-qe.io/badge/quality/lionagi/qe-fleet)
![Security](https://api.lionagi-qe.io/badge/security/lionagi/qe-fleet)
![Tests](https://api.lionagi-qe.io/badge/tests/lionagi/qe-fleet)
```

### HTML Integration

For more control, use HTML:

```html
<img src="https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet" alt="Coverage">
<img src="https://api.lionagi-qe.io/badge/quality/lionagi/qe-fleet" alt="Quality">
<img src="https://api.lionagi-qe.io/badge/security/lionagi/qe-fleet" alt="Security">
<img src="https://api.lionagi-qe.io/badge/tests/lionagi/qe-fleet" alt="Tests">
```

## API Endpoints

### Base URL

```
https://api.lionagi-qe.io/api/v1/badge
```

### Coverage Badge

```
GET /coverage/{org}/{repo}
```

**Parameters:**
- `style`: Badge style (`flat`, `flat-square`, `plastic`) - default: `flat`
- `color`: Custom color (hex without #) - optional
- `label`: Custom label text - optional

**Example:**
```
https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet?style=flat-square&color=97ca00
```

**Color Coding:**
- 🔴 Red (<60%): Needs improvement
- 🟡 Yellow (60-80%): Acceptable
- 🟢 Green (>80%): Excellent

### Quality Badge

```
GET /quality/{org}/{repo}
```

**Parameters:** Same as coverage badge

**Example:**
```
https://api.lionagi-qe.io/badge/quality/lionagi/qe-fleet?label=code%20quality
```

**Color Coding:**
- 🔴 Red (<70): Poor quality
- 🟡 Yellow (70-85): Needs improvement
- 🟢 Green (>85): High quality

### Security Badge

```
GET /security/{org}/{repo}
```

**Parameters:** Same as coverage badge

**Example:**
```
https://api.lionagi-qe.io/badge/security/lionagi/qe-fleet
```

**Display Modes:**
- Grade mode: Shows A+, A, B, C, D, F
- Vulnerability mode: Shows count (e.g., "2 critical")

### Tests Badge

```
GET /tests/{org}/{repo}
```

**Parameters:** Same as coverage badge

**Example:**
```
https://api.lionagi-qe.io/badge/tests/lionagi/qe-fleet
```

**Format:** Always green, shows formatted count (e.g., "1,234 passing")

## Badge Styles

### Flat (Default)

![Flat Style](https://img.shields.io/badge/coverage-85%25-brightgreen?style=flat)

```markdown
?style=flat
```

### Flat Square

![Flat Square Style](https://img.shields.io/badge/coverage-85%25-brightgreen?style=flat-square)

```markdown
?style=flat-square
```

### Plastic

![Plastic Style](https://img.shields.io/badge/coverage-85%25-brightgreen?style=plastic)

```markdown
?style=plastic
```

## Custom Colors

Override default color coding with custom hex colors:

```markdown
![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet?color=ff6b6b)
```

**Popular Colors:**
- Blue: `007ec6`
- Purple: `9f7aea`
- Orange: `ff6b6b`
- Pink: `ec4899`

## Custom Labels

Change the left-side label:

```markdown
![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet?label=test%20coverage)
```

**Note:** URL-encode spaces as `%20`

## CLI Usage

Generate badges locally using the CLI:

### Coverage Badge

```bash
aqe badge coverage \
  --project-id lionagi/qe-fleet \
  --percentage 85.5 \
  --output badge-coverage.svg
```

### Quality Badge

```bash
aqe badge quality \
  --project-id lionagi/qe-fleet \
  --score 92 \
  --output badge-quality.svg
```

### Security Badge

```bash
# Using grade
aqe badge security \
  --project-id lionagi/qe-fleet \
  --grade A+ \
  --output badge-security.svg

# Using vulnerability counts
aqe badge security \
  --project-id lionagi/qe-fleet \
  --critical 2 \
  --high 5 \
  --output badge-security.svg
```

### Tests Badge

```bash
aqe badge tests \
  --project-id lionagi/qe-fleet \
  --count 1234 \
  --output badge-tests.svg
```

### CLI Options

All badge commands support:
- `--style`: Badge style (`flat`, `flat-square`, `plastic`)
- `--color`: Custom color (hex)
- `--label`: Custom label text
- `--output`: Output file path

## Cache Management

### Invalidate Cached Badges

After updating metrics, invalidate badges to force regeneration:

```bash
# Invalidate all badges
aqe badge invalidate --project-id lionagi/qe-fleet

# Invalidate specific badge
aqe badge invalidate --project-id lionagi/qe-fleet --badge-type coverage
```

### Cache Statistics

View cache performance:

```bash
aqe badge cache-stats
```

### Clear Cache

```bash
aqe badge clear-cache
```

## Advanced Examples

### Badge Grid

Create a badge grid in your README:

```markdown
## Quality Metrics

| Metric | Status |
|--------|--------|
| Coverage | ![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet) |
| Quality | ![Quality](https://api.lionagi-qe.io/badge/quality/lionagi/qe-fleet) |
| Security | ![Security](https://api.lionagi-qe.io/badge/security/lionagi/qe-fleet) |
| Tests | ![Tests](https://api.lionagi-qe.io/badge/tests/lionagi/qe-fleet) |
```

### Inline Badges

Mix badges with text:

```markdown
This project maintains ![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet)
and has ![Quality](https://api.lionagi-qe.io/badge/quality/lionagi/qe-fleet).
```

### Link Badges to Reports

Make badges clickable:

```markdown
[![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet)](https://reports.lionagi-qe.io/coverage/lionagi/qe-fleet)
```

### Custom Styling

Combine multiple query parameters:

```markdown
![Custom](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet?style=flat-square&color=ec4899&label=test%20cov)
```

## Integration with CI/CD

### GitHub Actions

Update badges automatically after test runs:

```yaml
- name: Update Badge Cache
  run: |
    curl -X POST \
      https://api.lionagi-qe.io/api/v1/badge/invalidate/${{ github.repository }} \
      -H "Authorization: Bearer ${{ secrets.AQE_TOKEN }}"
```

### GitLab CI

```yaml
update_badges:
  script:
    - curl -X POST https://api.lionagi-qe.io/api/v1/badge/invalidate/${CI_PROJECT_PATH}
```

## Performance

- **Cache TTL**: 5 minutes
- **Response Time**: <100ms (cached), <500ms (uncached)
- **Update Latency**: Badges update within 5 minutes of test run
- **Concurrent Requests**: Unlimited

## Troubleshooting

### Badge Not Updating

1. Check cache invalidation:
   ```bash
   aqe badge invalidate -p your-org/your-repo
   ```

2. Verify API endpoint:
   ```bash
   curl https://api.lionagi-qe.io/badge/coverage/your-org/your-repo
   ```

### Badge Shows Wrong Data

Clear the cache:
```bash
aqe badge clear-cache
```

### Badge Not Rendering

1. Check URL encoding (spaces as `%20`)
2. Verify project ID format: `org/repo`
3. Test locally:
   ```bash
   aqe badge coverage -p org/repo -c 85 -o test.svg
   ```

## API Reference

### Response Headers

All badge endpoints return:
```
Content-Type: image/svg+xml
Cache-Control: max-age=300
X-Badge-Type: <badge-type>
```

### Error Responses

**404 Not Found**: Project not found
```json
{
  "error": "Project not found",
  "project_id": "org/repo"
}
```

**500 Internal Server Error**: Badge generation failed
```json
{
  "error": "Badge generation failed",
  "detail": "Error message"
}
```

## Best Practices

1. **Use Default Styles**: Stick with `flat` style for consistency
2. **Avoid Custom Colors**: Let color-coding reflect actual metrics
3. **Invalidate on Updates**: Clear cache after metric updates
4. **Link to Reports**: Make badges clickable to detailed reports
5. **Keep Labels Short**: Long labels make badges hard to read

## Examples Gallery

### Default Badges

![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
![Quality](https://img.shields.io/badge/quality-92%2F100-brightgreen)
![Security](https://img.shields.io/badge/security-A+-brightgreen)
![Tests](https://img.shields.io/badge/tests-1%2C234%20passing-brightgreen)

### Custom Styled

![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen?style=flat-square)
![Quality](https://img.shields.io/badge/code%20quality-92%2F100-brightgreen?style=flat-square)

### Warning States

![Coverage](https://img.shields.io/badge/coverage-65%25-yellow)
![Quality](https://img.shields.io/badge/quality-75%2F100-yellow)

### Error States

![Coverage](https://img.shields.io/badge/coverage-45%25-red)
![Security](https://img.shields.io/badge/security-2%20critical-red)

## Support

- **Documentation**: https://docs.lionagi-qe.io/badges
- **API Status**: https://status.lionagi-qe.io
- **Issues**: https://github.com/lionagi/qe-fleet/issues

---

**Version**: 1.0.0
**Last Updated**: 2025-11-12
**Service**: Agentic QE Fleet Badge Generation
