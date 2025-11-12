"""
Badge generation service for coverage, quality, and security scores.

Provides shields.io compatible SVG badges with caching and custom styling.
"""

from .generator import BadgeGenerator
from .colors import BadgeColors, get_color_for_coverage, get_color_for_quality
from .cache import BadgeCache

__all__ = [
    'BadgeGenerator',
    'BadgeColors',
    'BadgeCache',
    'get_color_for_coverage',
    'get_color_for_quality',
]

__version__ = '1.0.0'
