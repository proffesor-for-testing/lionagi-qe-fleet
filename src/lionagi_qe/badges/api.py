"""
HTTP API endpoints for badge generation.

Provides REST API for generating and serving badges.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from .generator import BadgeGenerator, BadgeType, BadgeStyle
from .cache import get_cache


# API Models
class BadgeRequest(BaseModel):
    """Request model for badge generation."""

    project_id: str = Field(..., description="Project identifier (org/repo)")
    style: BadgeStyle = Field('flat', description="Badge style")
    color: Optional[str] = Field(None, description="Custom color (hex)")
    label: Optional[str] = Field(None, description="Custom label text")


class BadgeResponse(BaseModel):
    """Response model for badge generation."""

    svg: str = Field(..., description="SVG badge content")
    cache_hit: bool = Field(..., description="Whether result was cached")


# Create router
router = APIRouter(prefix="/api/v1/badge", tags=["badges"])

# Global generator instance
generator = BadgeGenerator()


async def get_project_metrics(project_id: str, metric_type: str) -> Dict[str, Any]:
    """
    Fetch project metrics from artifact storage.

    Args:
        project_id: Project identifier
        metric_type: Type of metric (coverage, quality, security, tests)

    Returns:
        Metric data dictionary

    Note:
        This is a placeholder. In production, this would integrate with
        the artifact storage service to fetch latest metrics.
    """
    # TODO: Integrate with artifact storage service
    # For now, return mock data
    mock_data = {
        'coverage': {'percentage': 85.5},
        'quality': {'score': 92},
        'security': {'grade': 'A+'},
        'tests': {'passing': 1234},
    }

    return mock_data.get(metric_type, {})


@router.get(
    "/coverage/{org}/{repo}",
    response_class=Response,
    responses={
        200: {"content": {"image/svg+xml": {}}},
    }
)
async def get_coverage_badge(
    org: str,
    repo: str,
    style: BadgeStyle = Query('flat', description="Badge style"),
    color: Optional[str] = Query(None, description="Custom color (hex)"),
    label: Optional[str] = Query(None, description="Custom label"),
) -> Response:
    """
    Generate coverage badge.

    Returns SVG badge showing test coverage percentage.

    Color coding:
    - Red (<60%): Needs improvement
    - Yellow (60-80%): Acceptable
    - Green (>80%): Excellent
    """
    project_id = f"{org}/{repo}"

    try:
        # Fetch coverage data
        coverage_data = await get_project_metrics(project_id, 'coverage')

        # Generate badge
        svg = await generator.generate_coverage_badge(
            project_id=project_id,
            coverage_data=coverage_data,
            style=style,
            custom_color=color,
            custom_label=label,
        )

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "max-age=300",  # 5 minutes
                "X-Badge-Type": "coverage",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/{org}/{repo}",
    response_class=Response,
    responses={
        200: {"content": {"image/svg+xml": {}}},
    }
)
async def get_quality_badge(
    org: str,
    repo: str,
    style: BadgeStyle = Query('flat', description="Badge style"),
    color: Optional[str] = Query(None, description="Custom color (hex)"),
    label: Optional[str] = Query(None, description="Custom label"),
) -> Response:
    """
    Generate quality score badge.

    Returns SVG badge showing overall quality score (0-100).

    Color coding:
    - Red (<70): Poor quality
    - Yellow (70-85): Needs improvement
    - Green (>85): High quality
    """
    project_id = f"{org}/{repo}"

    try:
        # Fetch quality data
        quality_data = await get_project_metrics(project_id, 'quality')

        # Generate badge
        svg = await generator.generate_quality_badge(
            project_id=project_id,
            quality_data=quality_data,
            style=style,
            custom_color=color,
            custom_label=label,
        )

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "max-age=300",
                "X-Badge-Type": "quality",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/security/{org}/{repo}",
    response_class=Response,
    responses={
        200: {"content": {"image/svg+xml": {}}},
    }
)
async def get_security_badge(
    org: str,
    repo: str,
    style: BadgeStyle = Query('flat', description="Badge style"),
    color: Optional[str] = Query(None, description="Custom color (hex)"),
    label: Optional[str] = Query(None, description="Custom label"),
) -> Response:
    """
    Generate security badge.

    Returns SVG badge showing security grade or vulnerability counts.

    Shows either:
    - Security grade (A+, A, B, C, D, F)
    - Vulnerability count (e.g., "2 critical")
    """
    project_id = f"{org}/{repo}"

    try:
        # Fetch security data
        security_data = await get_project_metrics(project_id, 'security')

        # Generate badge
        svg = await generator.generate_security_badge(
            project_id=project_id,
            security_data=security_data,
            style=style,
            custom_color=color,
            custom_label=label,
        )

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "max-age=300",
                "X-Badge-Type": "security",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tests/{org}/{repo}",
    response_class=Response,
    responses={
        200: {"content": {"image/svg+xml": {}}},
    }
)
async def get_tests_badge(
    org: str,
    repo: str,
    style: BadgeStyle = Query('flat', description="Badge style"),
    color: Optional[str] = Query(None, description="Custom color (hex)"),
    label: Optional[str] = Query(None, description="Custom label"),
) -> Response:
    """
    Generate tests badge.

    Returns SVG badge showing total passing test count.

    Always displays in green with formatted count (e.g., "1,234 passing").
    """
    project_id = f"{org}/{repo}"

    try:
        # Fetch test data
        test_data = await get_project_metrics(project_id, 'tests')

        # Generate badge
        svg = await generator.generate_tests_badge(
            project_id=project_id,
            test_data=test_data,
            style=style,
            custom_color=color,
            custom_label=label,
        )

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "max-age=300",
                "X-Badge-Type": "tests",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate/{org}/{repo}")
async def invalidate_badges(
    org: str,
    repo: str,
    badge_type: Optional[BadgeType] = Query(None, description="Specific badge type"),
) -> Dict[str, Any]:
    """
    Invalidate cached badges for a project.

    Use this endpoint after updating metrics to force badge regeneration.
    """
    project_id = f"{org}/{repo}"

    try:
        count = generator.invalidate_cache(project_id, badge_type)

        return {
            "project_id": project_id,
            "badge_type": badge_type or "all",
            "invalidated": count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get badge cache statistics.

    Returns information about cache size and performance.
    """
    cache = get_cache()
    return cache.stats()
