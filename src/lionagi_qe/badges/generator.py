"""
Badge generation service with shields.io compatible format.

Generates SVG badges for coverage, quality, security, and test counts.
"""

import os
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .colors import (
    BadgeColors,
    BadgeStyle,
    get_color_for_coverage,
    get_color_for_quality,
    get_color_for_security_grade,
    get_color_for_vulnerabilities,
    format_number,
    format_percentage,
)
from .cache import BadgeCache, get_cache


BadgeType = Literal['coverage', 'quality', 'security', 'tests']


class BadgeGenerator:
    """
    Generate shields.io compatible SVG badges.

    Attributes:
        cache: Badge cache instance
        template_dir: Directory containing SVG templates
    """

    def __init__(self, cache: Optional[BadgeCache] = None):
        """
        Initialize badge generator.

        Args:
            cache: Badge cache instance (uses global cache if None)
        """
        self.cache = cache or get_cache()

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / 'templates'
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['svg']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _calculate_dimensions(
        self,
        label: str,
        message: str,
        style: BadgeStyle = 'flat'
    ) -> Dict[str, int]:
        """
        Calculate SVG dimensions based on text length.

        Args:
            label: Left side label text
            message: Right side message text
            style: Badge style

        Returns:
            Dictionary with dimension values
        """
        # Approximate character width (pixels)
        char_width = 6

        # Calculate text lengths
        label_length = len(label) * char_width * 10
        message_length = len(message) * char_width * 10

        # Add padding
        label_width = (len(label) * char_width) + 10
        message_width = (len(message) * char_width) + 10

        total_width = label_width + message_width

        # Calculate text positions (centered)
        label_x = (label_width * 10) // 2
        message_x = (label_width * 10) + (message_width * 10) // 2

        return {
            'width': total_width,
            'label_width': label_width,
            'message_width': message_width,
            'label_x': label_x,
            'message_x': message_x,
            'label_text_length': label_length,
            'message_text_length': message_length,
        }

    def _render_badge(
        self,
        label: str,
        message: str,
        color: str,
        style: BadgeStyle = 'flat'
    ) -> str:
        """
        Render SVG badge from template.

        Args:
            label: Left side label
            message: Right side message
            color: Badge color (hex)
            style: Badge style

        Returns:
            SVG string
        """
        dimensions = self._calculate_dimensions(label, message, style)

        # Select template based on style
        template_name = 'flat-square.svg.j2' if style == 'flat-square' else 'base.svg.j2'
        template = self.jinja_env.get_template(template_name)

        return template.render(
            label=label,
            message=message,
            color=color,
            **dimensions
        )

    async def generate_coverage_badge(
        self,
        project_id: str,
        coverage_data: Dict[str, Any],
        style: BadgeStyle = 'flat',
        custom_color: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> str:
        """
        Generate coverage badge.

        Args:
            project_id: Project identifier
            coverage_data: Coverage data with 'percentage' key
            style: Badge style
            custom_color: Custom color override
            custom_label: Custom label override

        Returns:
            SVG badge string

        Example:
            >>> await generator.generate_coverage_badge(
            ...     'lionagi/qe-fleet',
            ...     {'percentage': 85.5},
            ... )
            '<svg>...</svg>'
        """
        percentage = coverage_data.get('percentage', 0)
        label = custom_label or 'coverage'
        message = format_percentage(percentage)

        color = custom_color or get_color_for_coverage(percentage)

        # Check cache
        cache_key = f"{project_id}:coverage:{style}:{color}:{label}"
        cached = self.cache.get(project_id, 'coverage', style=style, color=color, label=label)
        if cached:
            return cached

        # Generate badge
        svg = self._render_badge(label, message, color, style)

        # Cache result
        self.cache.set(project_id, 'coverage', svg, style=style, color=color, label=label)

        return svg

    async def generate_quality_badge(
        self,
        project_id: str,
        quality_data: Dict[str, Any],
        style: BadgeStyle = 'flat',
        custom_color: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> str:
        """
        Generate quality score badge.

        Args:
            project_id: Project identifier
            quality_data: Quality data with 'score' key (0-100)
            style: Badge style
            custom_color: Custom color override
            custom_label: Custom label override

        Returns:
            SVG badge string
        """
        score = quality_data.get('score', 0)
        label = custom_label or 'quality'
        message = f"{int(score)}/100"

        color = custom_color or get_color_for_quality(score)

        # Check cache
        cached = self.cache.get(project_id, 'quality', style=style, color=color, label=label)
        if cached:
            return cached

        # Generate badge
        svg = self._render_badge(label, message, color, style)

        # Cache result
        self.cache.set(project_id, 'quality', svg, style=style, color=color, label=label)

        return svg

    async def generate_security_badge(
        self,
        project_id: str,
        security_data: Dict[str, Any],
        style: BadgeStyle = 'flat',
        custom_color: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> str:
        """
        Generate security badge.

        Args:
            project_id: Project identifier
            security_data: Security data with 'grade' or vulnerability counts
            style: Badge style
            custom_color: Custom color override
            custom_label: Custom label override

        Returns:
            SVG badge string

        Security data formats:
            - Grade: {'grade': 'A+'}
            - Vulnerabilities: {'critical': 0, 'high': 1, 'medium': 3}
        """
        label = custom_label or 'security'

        # Check if using grade system
        if 'grade' in security_data:
            grade = security_data['grade']
            message = grade
            color = custom_color or get_color_for_security_grade(grade)
        else:
            # Use vulnerability counts
            critical = security_data.get('critical', 0)
            high = security_data.get('high', 0)
            medium = security_data.get('medium', 0)

            if critical > 0:
                message = f"{critical} critical"
            elif high > 0:
                message = f"{high} high"
            elif medium > 0:
                message = f"{medium} medium"
            else:
                message = "passing"

            color = custom_color or get_color_for_vulnerabilities(critical, high, medium)

        # Check cache
        cached = self.cache.get(project_id, 'security', style=style, color=color, label=label)
        if cached:
            return cached

        # Generate badge
        svg = self._render_badge(label, message, color, style)

        # Cache result
        self.cache.set(project_id, 'security', svg, style=style, color=color, label=label)

        return svg

    async def generate_tests_badge(
        self,
        project_id: str,
        test_data: Dict[str, Any],
        style: BadgeStyle = 'flat',
        custom_color: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> str:
        """
        Generate test count badge.

        Args:
            project_id: Project identifier
            test_data: Test data with 'total' or 'passing' keys
            style: Badge style
            custom_color: Custom color override
            custom_label: Custom label override

        Returns:
            SVG badge string
        """
        total = test_data.get('passing', test_data.get('total', 0))
        label = custom_label or 'tests'
        message = f"{format_number(total)} passing"

        # Tests badge is always green
        color = custom_color or BadgeColors.PASSING

        # Check cache
        cached = self.cache.get(project_id, 'tests', style=style, color=color, label=label)
        if cached:
            return cached

        # Generate badge
        svg = self._render_badge(label, message, color, style)

        # Cache result
        self.cache.set(project_id, 'tests', svg, style=style, color=color, label=label)

        return svg

    async def generate_badge(
        self,
        badge_type: BadgeType,
        project_id: str,
        data: Dict[str, Any],
        style: BadgeStyle = 'flat',
        custom_color: Optional[str] = None,
        custom_label: Optional[str] = None,
    ) -> str:
        """
        Generate badge of any type.

        Args:
            badge_type: Type of badge to generate
            project_id: Project identifier
            data: Badge-specific data
            style: Badge style
            custom_color: Custom color override
            custom_label: Custom label override

        Returns:
            SVG badge string

        Raises:
            ValueError: If badge_type is invalid
        """
        if badge_type == 'coverage':
            return await self.generate_coverage_badge(
                project_id=project_id,
                coverage_data=data,
                style=style,
                custom_color=custom_color,
                custom_label=custom_label,
            )
        elif badge_type == 'quality':
            return await self.generate_quality_badge(
                project_id=project_id,
                quality_data=data,
                style=style,
                custom_color=custom_color,
                custom_label=custom_label,
            )
        elif badge_type == 'security':
            return await self.generate_security_badge(
                project_id=project_id,
                security_data=data,
                style=style,
                custom_color=custom_color,
                custom_label=custom_label,
            )
        elif badge_type == 'tests':
            return await self.generate_tests_badge(
                project_id=project_id,
                test_data=data,
                style=style,
                custom_color=custom_color,
                custom_label=custom_label,
            )
        else:
            raise ValueError(f"Invalid badge type: {badge_type}")

    def invalidate_cache(
        self,
        project_id: str,
        badge_type: Optional[BadgeType] = None
    ) -> int:
        """
        Invalidate cached badges.

        Args:
            project_id: Project identifier
            badge_type: Specific badge type (or None for all)

        Returns:
            Number of cache entries invalidated
        """
        return self.cache.invalidate(project_id, badge_type)
