"""
CLI commands for badge generation.

Provides command-line interface for generating badges locally.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from .generator import BadgeGenerator, BadgeType, BadgeStyle
from .cache import get_cache


@click.group(name='badge')
def badge_cli():
    """Generate SVG badges for coverage, quality, security, and tests."""
    pass


@badge_cli.command()
@click.option('--project-id', '-p', required=True, help='Project identifier (org/repo)')
@click.option('--percentage', '-c', type=float, required=True, help='Coverage percentage')
@click.option('--style', '-s', type=click.Choice(['flat', 'flat-square', 'plastic']), default='flat', help='Badge style')
@click.option('--color', help='Custom color (hex)')
@click.option('--label', help='Custom label')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def coverage(
    project_id: str,
    percentage: float,
    style: str,
    color: Optional[str],
    label: Optional[str],
    output: Optional[str]
):
    """
    Generate coverage badge.

    Example:
        aqe badge coverage -p lionagi/qe-fleet -c 85.5 -o badge-coverage.svg
    """
    async def _generate():
        generator = BadgeGenerator()
        svg = await generator.generate_coverage_badge(
            project_id=project_id,
            coverage_data={'percentage': percentage},
            style=style,  # type: ignore
            custom_color=color,
            custom_label=label,
        )

        if output:
            Path(output).write_text(svg)
            click.echo(f"✓ Coverage badge saved to: {output}")
        else:
            click.echo(svg)

    asyncio.run(_generate())


@badge_cli.command()
@click.option('--project-id', '-p', required=True, help='Project identifier (org/repo)')
@click.option('--score', '-s', type=float, required=True, help='Quality score (0-100)')
@click.option('--style', type=click.Choice(['flat', 'flat-square', 'plastic']), default='flat', help='Badge style')
@click.option('--color', help='Custom color (hex)')
@click.option('--label', help='Custom label')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def quality(
    project_id: str,
    score: float,
    style: str,
    color: Optional[str],
    label: Optional[str],
    output: Optional[str]
):
    """
    Generate quality score badge.

    Example:
        aqe badge quality -p lionagi/qe-fleet -s 92 -o badge-quality.svg
    """
    async def _generate():
        generator = BadgeGenerator()
        svg = await generator.generate_quality_badge(
            project_id=project_id,
            quality_data={'score': score},
            style=style,  # type: ignore
            custom_color=color,
            custom_label=label,
        )

        if output:
            Path(output).write_text(svg)
            click.echo(f"✓ Quality badge saved to: {output}")
        else:
            click.echo(svg)

    asyncio.run(_generate())


@badge_cli.command()
@click.option('--project-id', '-p', required=True, help='Project identifier (org/repo)')
@click.option('--grade', '-g', help='Security grade (A+, A, B, C, D, F)')
@click.option('--critical', type=int, default=0, help='Critical vulnerabilities')
@click.option('--high', type=int, default=0, help='High severity vulnerabilities')
@click.option('--medium', type=int, default=0, help='Medium severity vulnerabilities')
@click.option('--style', type=click.Choice(['flat', 'flat-square', 'plastic']), default='flat', help='Badge style')
@click.option('--color', help='Custom color (hex)')
@click.option('--label', help='Custom label')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def security(
    project_id: str,
    grade: Optional[str],
    critical: int,
    high: int,
    medium: int,
    style: str,
    color: Optional[str],
    label: Optional[str],
    output: Optional[str]
):
    """
    Generate security badge.

    Can use either grade or vulnerability counts.

    Examples:
        aqe badge security -p lionagi/qe-fleet -g A+ -o badge-security.svg
        aqe badge security -p lionagi/qe-fleet --critical 2 --high 5
    """
    if not grade and critical == 0 and high == 0 and medium == 0:
        click.echo("Error: Must provide either --grade or vulnerability counts", err=True)
        sys.exit(1)

    async def _generate():
        generator = BadgeGenerator()

        if grade:
            security_data = {'grade': grade}
        else:
            security_data = {
                'critical': critical,
                'high': high,
                'medium': medium,
            }

        svg = await generator.generate_security_badge(
            project_id=project_id,
            security_data=security_data,
            style=style,  # type: ignore
            custom_color=color,
            custom_label=label,
        )

        if output:
            Path(output).write_text(svg)
            click.echo(f"✓ Security badge saved to: {output}")
        else:
            click.echo(svg)

    asyncio.run(_generate())


@badge_cli.command()
@click.option('--project-id', '-p', required=True, help='Project identifier (org/repo)')
@click.option('--count', '-c', type=int, required=True, help='Test count')
@click.option('--style', type=click.Choice(['flat', 'flat-square', 'plastic']), default='flat', help='Badge style')
@click.option('--color', help='Custom color (hex)')
@click.option('--label', help='Custom label')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def tests(
    project_id: str,
    count: int,
    style: str,
    color: Optional[str],
    label: Optional[str],
    output: Optional[str]
):
    """
    Generate test count badge.

    Example:
        aqe badge tests -p lionagi/qe-fleet -c 1234 -o badge-tests.svg
    """
    async def _generate():
        generator = BadgeGenerator()
        svg = await generator.generate_tests_badge(
            project_id=project_id,
            test_data={'passing': count},
            style=style,  # type: ignore
            custom_color=color,
            custom_label=label,
        )

        if output:
            Path(output).write_text(svg)
            click.echo(f"✓ Tests badge saved to: {output}")
        else:
            click.echo(svg)

    asyncio.run(_generate())


@badge_cli.command()
@click.option('--project-id', '-p', required=True, help='Project identifier (org/repo)')
@click.option('--badge-type', '-t', type=click.Choice(['coverage', 'quality', 'security', 'tests', 'all']), default='all', help='Badge type to invalidate')
def invalidate(project_id: str, badge_type: str):
    """
    Invalidate cached badges.

    Example:
        aqe badge invalidate -p lionagi/qe-fleet -t coverage
    """
    cache = get_cache()
    count = cache.invalidate(project_id, None if badge_type == 'all' else badge_type)  # type: ignore

    click.echo(f"✓ Invalidated {count} badge(s) for {project_id}")


@badge_cli.command()
def cache_stats():
    """Display badge cache statistics."""
    cache = get_cache()
    stats = cache.stats()

    click.echo("\nBadge Cache Statistics:")
    click.echo(f"  Total entries:  {stats['total_entries']}")
    click.echo(f"  Active entries: {stats['active_entries']}")
    click.echo(f"  Expired:        {stats['expired_entries']}")
    click.echo(f"  Default TTL:    {stats['default_ttl']}s")


@badge_cli.command()
def clear_cache():
    """Clear all cached badges."""
    cache = get_cache()
    cache.clear()
    click.echo("✓ Cache cleared")


if __name__ == '__main__':
    badge_cli()
