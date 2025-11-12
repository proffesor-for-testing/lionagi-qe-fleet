# Badge Generation - Quick Reference Card

One-page reference for badge generation service.

## 📝 Quick Start

### Markdown
```markdown
![Coverage](https://api.lionagi-qe.io/badge/coverage/org/repo)
![Quality](https://api.lionagi-qe.io/badge/quality/org/repo)
![Security](https://api.lionagi-qe.io/badge/security/org/repo)
![Tests](https://api.lionagi-qe.io/badge/tests/org/repo)
```

### CLI
```bash
aqe badge coverage -p org/repo -c 85.5 -o badge.svg
aqe badge quality -p org/repo -s 92 -o badge.svg
aqe badge security -p org/repo -g A+ -o badge.svg
aqe badge tests -p org/repo -c 1234 -o badge.svg
```

## 🎨 Badge Types

| Badge | Format | Color Coding |
|-------|--------|--------------|
| **Coverage** | `coverage \| 85.5%` | 🔴 <60% 🟡 60-80% 🟢 >80% |
| **Quality** | `quality \| 92/100` | 🔴 <70 🟡 70-85 🟢 >85 |
| **Security** | `security \| A+` | 🟢 A+ 🔴 F or "2 critical" |
| **Tests** | `tests \| 1,234 passing` | 🟢 Always green |

## 🔧 Customization

### Styles
```
?style=flat              # Default with gradient
?style=flat-square       # Minimal flat design
?style=plastic           # 3D-style
```

### Colors
```
?color=4c1               # Custom hex color
?color=ff6b6b            # Orange
?color=ec4899            # Pink
```

### Labels
```
?label=test%20coverage   # Custom label (URL-encode spaces)
```

### Combined
```
?style=flat-square&color=ec4899&label=coverage
```

## 🚀 API Endpoints

```
GET  /api/v1/badge/coverage/{org}/{repo}
GET  /api/v1/badge/quality/{org}/{repo}
GET  /api/v1/badge/security/{org}/{repo}
GET  /api/v1/badge/tests/{org}/{repo}
POST /api/v1/badge/invalidate/{org}/{repo}
GET  /api/v1/badge/cache/stats
```

## 💾 Cache Management

```bash
# View cache stats
aqe badge cache-stats

# Invalidate specific badge
aqe badge invalidate -p org/repo -t coverage

# Invalidate all badges
aqe badge invalidate -p org/repo

# Clear entire cache
aqe badge clear-cache
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Cache hit | <50ms |
| Cache miss | <300ms |
| Cache TTL | 5 minutes |
| Badge size | ~1.2 KB |

## 🔗 Integration Examples

### README Table
```markdown
| Metric | Status |
|--------|--------|
| Coverage | ![Coverage](https://api.lionagi-qe.io/badge/coverage/org/repo) |
| Quality | ![Quality](https://api.lionagi-qe.io/badge/quality/org/repo) |
```

### Clickable Badge
```markdown
[![Coverage](https://api.lionagi-qe.io/badge/coverage/org/repo)](https://reports.org/coverage)
```

### GitHub Actions
```yaml
- name: Update Badges
  run: |
    curl -X POST https://api.lionagi-qe.io/api/v1/badge/invalidate/${{ github.repository }}
```

## 📦 Dependencies

**Production**: fastapi, uvicorn, jinja2, click, pydantic
**Development**: pytest, pytest-asyncio
**External APIs**: None (self-contained)

## 🐍 Programmatic Usage

```python
from lionagi_qe.badges.generator import BadgeGenerator

generator = BadgeGenerator()

svg = await generator.generate_coverage_badge(
    project_id='org/repo',
    coverage_data={'percentage': 85.5}
)

# Save to file
Path('badge.svg').write_text(svg)
```

## 🛠️ Troubleshooting

### Badge not updating?
```bash
aqe badge invalidate -p org/repo
```

### Wrong data shown?
```bash
aqe badge clear-cache
```

### Test locally?
```bash
aqe badge coverage -p org/repo -c 85 -o test.svg
```

## 📖 Documentation

- Integration Guide: `/docs/badge-integration-guide.md`
- API Spec: `/docs/api/badge-api-spec.md`
- Implementation: `/docs/badge-implementation-summary.md`
- Report: `/docs/badge-generation-report.md`

## ✅ Success Criteria

- ✅ Render correctly in GitHub/GitLab
- ✅ Update within 5 minutes
- ✅ Support custom colors/styles
- ✅ <100ms response time (cached)
- ✅ Works without external dependencies

---

**Version**: 1.0.0 | **Status**: Production Ready | **Date**: 2025-11-12
