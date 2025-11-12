# Badge Generation API Specification

Version: 1.0.0
Base URL: `https://api.lionagi-qe.io/api/v1/badge`

## Overview

REST API for generating shields.io compatible SVG badges for quality metrics.

## Authentication

Currently public (no authentication required).

Future versions may require API key for rate limiting.

## Rate Limits

- **Free tier**: 60 requests/minute
- **Cached responses**: Not counted against rate limit
- **Cache TTL**: 5 minutes

## Endpoints

### GET /coverage/{org}/{repo}

Generate coverage badge.

**Path Parameters:**
- `org` (string, required): Organization name
- `repo` (string, required): Repository name

**Query Parameters:**
- `style` (string, optional): Badge style
  - Values: `flat`, `flat-square`, `plastic`
  - Default: `flat`
- `color` (string, optional): Custom color (hex without #)
  - Example: `4c1` or `brightgreen`
- `label` (string, optional): Custom label text
  - Default: `coverage`

**Response:**
- Content-Type: `image/svg+xml`
- Status: 200 OK
- Headers:
  - `Cache-Control: max-age=300`
  - `X-Badge-Type: coverage`

**Example Request:**
```bash
curl https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet
```

**Example Response:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20">
  <!-- SVG content -->
</svg>
```

**Color Coding:**
| Percentage | Color | Meaning |
|------------|-------|---------|
| < 60% | Red (#e05d44) | Needs improvement |
| 60-80% | Yellow (#dfb317) | Acceptable |
| > 80% | Green (#4c1) | Excellent |

---

### GET /quality/{org}/{repo}

Generate quality score badge.

**Path Parameters:**
- `org` (string, required): Organization name
- `repo` (string, required): Repository name

**Query Parameters:**
Same as coverage endpoint.

**Response:**
Same format as coverage endpoint.

**Color Coding:**
| Score | Color | Meaning |
|-------|-------|---------|
| < 70 | Red (#e05d44) | Poor quality |
| 70-85 | Yellow (#dfb317) | Needs improvement |
| > 85 | Green (#4c1) | High quality |

---

### GET /security/{org}/{repo}

Generate security badge.

**Path Parameters:**
- `org` (string, required): Organization name
- `repo` (string, required): Repository name

**Query Parameters:**
Same as coverage endpoint.

**Response:**
Same format as coverage endpoint.

**Display Modes:**

1. **Grade Mode** (when grade available):
   - Format: `A+`, `A`, `B`, `C`, `D`, `F`
   - Color: Based on grade

2. **Vulnerability Mode** (when counts available):
   - Format: `2 critical`, `5 high`, `3 medium`, `passing`
   - Color: Based on severity

**Color Coding:**
| Grade | Color | Vulnerabilities | Color |
|-------|-------|-----------------|-------|
| A+ | #00b140 | 0 | Green (#4c1) |
| A | #4c1 | Medium only | Blue (#007ec6) |
| B | #97ca00 | High | Yellow (#dfb317) |
| C | #dfb317 | Critical | Red (#e05d44) |
| D | #fe7d37 | | |
| F | #e05d44 | | |

---

### GET /tests/{org}/{repo}

Generate test count badge.

**Path Parameters:**
- `org` (string, required): Organization name
- `repo` (string, required): Repository name

**Query Parameters:**
Same as coverage endpoint.

**Response:**
Same format as coverage endpoint.

**Format:**
- Always green
- Shows formatted count: `1,234 passing`

---

### POST /invalidate/{org}/{repo}

Invalidate cached badges.

**Path Parameters:**
- `org` (string, required): Organization name
- `repo` (string, required): Repository name

**Query Parameters:**
- `badge_type` (string, optional): Specific badge type
  - Values: `coverage`, `quality`, `security`, `tests`
  - Default: All badges

**Response:**
```json
{
  "project_id": "lionagi/qe-fleet",
  "badge_type": "coverage",
  "invalidated": 1
}
```

**Example Request:**
```bash
curl -X POST \
  https://api.lionagi-qe.io/api/v1/badge/invalidate/lionagi/qe-fleet?badge_type=coverage
```

---

### GET /cache/stats

Get cache statistics.

**Response:**
```json
{
  "total_entries": 150,
  "active_entries": 142,
  "expired_entries": 8,
  "default_ttl": 300
}
```

## Error Responses

### 400 Bad Request

Invalid parameters.

```json
{
  "detail": "Invalid style parameter"
}
```

### 404 Not Found

Project not found.

```json
{
  "detail": "Project not found",
  "project_id": "org/repo"
}
```

### 429 Too Many Requests

Rate limit exceeded.

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error

Badge generation failed.

```json
{
  "detail": "Badge generation failed"
}
```

## Examples

### Basic Usage

```bash
# Coverage badge
curl https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet

# Quality badge
curl https://api.lionagi-qe.io/api/v1/badge/quality/lionagi/qe-fleet

# Security badge
curl https://api.lionagi-qe.io/api/v1/badge/security/lionagi/qe-fleet

# Tests badge
curl https://api.lionagi-qe.io/api/v1/badge/tests/lionagi/qe-fleet
```

### Custom Styling

```bash
# Flat square style
curl "https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet?style=flat-square"

# Custom color
curl "https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet?color=ff6b6b"

# Custom label
curl "https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet?label=test%20cov"

# Combined
curl "https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet?style=flat-square&color=ec4899&label=coverage"
```

### Cache Management

```bash
# Invalidate all badges
curl -X POST https://api.lionagi-qe.io/api/v1/badge/invalidate/lionagi/qe-fleet

# Invalidate specific badge
curl -X POST "https://api.lionagi-qe.io/api/v1/badge/invalidate/lionagi/qe-fleet?badge_type=coverage"

# Get cache stats
curl https://api.lionagi-qe.io/api/v1/badge/cache/stats
```

## Performance

### Response Times

| Scenario | Response Time |
|----------|---------------|
| Cache hit | < 50ms |
| Cache miss | < 300ms |
| Cold start | < 500ms |

### Caching Strategy

- **TTL**: 5 minutes (300 seconds)
- **Cache key**: `{org}/{repo}:{badge_type}:{style}:{color}:{label}`
- **Storage**: In-memory (per instance)
- **Invalidation**: Manual via POST endpoint

### Optimization

- Badges are pre-rendered and cached
- SVG templates are compiled once
- Dimension calculations are cached
- Thread-safe cache implementation

## Integration

### HTML

```html
<img src="https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet"
     alt="Coverage">
```

### Markdown

```markdown
![Coverage](https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet)
```

### reStructuredText

```rst
.. image:: https://api.lionagi-qe.io/api/v1/badge/coverage/lionagi/qe-fleet
   :alt: Coverage
```

## OpenAPI Schema

Full OpenAPI 3.0 schema available at:
```
https://api.lionagi-qe.io/api/v1/badge/openapi.json
```

Interactive documentation:
```
https://api.lionagi-qe.io/api/v1/badge/docs
```

## Support

- **Documentation**: https://docs.lionagi-qe.io/badges
- **API Status**: https://status.lionagi-qe.io
- **Rate Limit Info**: Check `X-RateLimit-*` headers

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
