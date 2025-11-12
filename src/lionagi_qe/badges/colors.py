"""
Color schemes and utilities for badge generation.

Provides color-coding logic based on metrics thresholds.
"""

from typing import Literal

BadgeStyle = Literal['flat', 'flat-square', 'plastic', 'for-the-badge']


class BadgeColors:
    """Standard badge color schemes."""

    # Status colors
    SUCCESS = '#4c1'  # Bright green
    WARNING = '#dfb317'  # Yellow
    ERROR = '#e05d44'  # Red
    INFO = '#007ec6'  # Blue
    NEUTRAL = '#9f9f9f'  # Gray

    # Security grades
    GRADE_A_PLUS = '#00b140'  # Excellent
    GRADE_A = '#4c1'  # Good
    GRADE_B = '#97ca00'  # Acceptable
    GRADE_C = '#dfb317'  # Needs work
    GRADE_D = '#fe7d37'  # Poor
    GRADE_F = '#e05d44'  # Critical

    # Custom colors
    PASSING = '#4c1'
    FAILING = '#e05d44'


def get_color_for_coverage(percentage: float) -> str:
    """
    Get color based on coverage percentage.

    Args:
        percentage: Coverage percentage (0-100)

    Returns:
        Hex color code

    Thresholds:
        - <60%: Red (needs improvement)
        - 60-80%: Yellow (acceptable)
        - >80%: Green (excellent)
    """
    if percentage < 60:
        return BadgeColors.ERROR
    elif percentage < 80:
        return BadgeColors.WARNING
    else:
        return BadgeColors.SUCCESS


def get_color_for_quality(score: float) -> str:
    """
    Get color based on quality score.

    Args:
        score: Quality score (0-100)

    Returns:
        Hex color code

    Thresholds:
        - <70: Red (poor quality)
        - 70-85: Yellow (needs improvement)
        - >85: Green (high quality)
    """
    if score < 70:
        return BadgeColors.ERROR
    elif score < 85:
        return BadgeColors.WARNING
    else:
        return BadgeColors.SUCCESS


def get_color_for_security_grade(grade: str) -> str:
    """
    Get color based on security grade.

    Args:
        grade: Security grade (A+, A, B, C, D, F)

    Returns:
        Hex color code
    """
    grade_map = {
        'A+': BadgeColors.GRADE_A_PLUS,
        'A': BadgeColors.GRADE_A,
        'B': BadgeColors.GRADE_B,
        'C': BadgeColors.GRADE_C,
        'D': BadgeColors.GRADE_D,
        'F': BadgeColors.GRADE_F,
    }
    return grade_map.get(grade.upper(), BadgeColors.NEUTRAL)


def get_color_for_vulnerabilities(critical: int, high: int, medium: int) -> str:
    """
    Get color based on vulnerability counts.

    Args:
        critical: Number of critical vulnerabilities
        high: Number of high severity vulnerabilities
        medium: Number of medium severity vulnerabilities

    Returns:
        Hex color code
    """
    if critical > 0:
        return BadgeColors.ERROR
    elif high > 0:
        return BadgeColors.WARNING
    elif medium > 0:
        return BadgeColors.INFO
    else:
        return BadgeColors.SUCCESS


def format_number(num: int) -> str:
    """
    Format number with thousand separators.

    Args:
        num: Number to format

    Returns:
        Formatted string (e.g., "1,234")
    """
    return f"{num:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage value.

    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"
