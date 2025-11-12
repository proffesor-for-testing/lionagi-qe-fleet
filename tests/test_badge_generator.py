"""
Tests for badge generation service.

Tests all badge types, caching, and error handling.
"""

import pytest
from unittest.mock import Mock, patch

from lionagi_qe.badges.generator import BadgeGenerator
from lionagi_qe.badges.colors import (
    BadgeColors,
    get_color_for_coverage,
    get_color_for_quality,
    get_color_for_security_grade,
    get_color_for_vulnerabilities,
)
from lionagi_qe.badges.cache import BadgeCache


class TestBadgeColors:
    """Test color scheme utilities."""

    def test_coverage_colors(self):
        """Test coverage color thresholds."""
        assert get_color_for_coverage(50) == BadgeColors.ERROR  # <60%
        assert get_color_for_coverage(70) == BadgeColors.WARNING  # 60-80%
        assert get_color_for_coverage(90) == BadgeColors.SUCCESS  # >80%

    def test_quality_colors(self):
        """Test quality score colors."""
        assert get_color_for_quality(60) == BadgeColors.ERROR  # <70
        assert get_color_for_quality(75) == BadgeColors.WARNING  # 70-85
        assert get_color_for_quality(95) == BadgeColors.SUCCESS  # >85

    def test_security_grade_colors(self):
        """Test security grade colors."""
        assert get_color_for_security_grade('A+') == BadgeColors.GRADE_A_PLUS
        assert get_color_for_security_grade('A') == BadgeColors.GRADE_A
        assert get_color_for_security_grade('B') == BadgeColors.GRADE_B
        assert get_color_for_security_grade('F') == BadgeColors.GRADE_F

    def test_vulnerability_colors(self):
        """Test vulnerability-based colors."""
        # Critical vulnerabilities
        assert get_color_for_vulnerabilities(1, 0, 0) == BadgeColors.ERROR

        # High vulnerabilities
        assert get_color_for_vulnerabilities(0, 1, 0) == BadgeColors.WARNING

        # Medium vulnerabilities
        assert get_color_for_vulnerabilities(0, 0, 1) == BadgeColors.INFO

        # No vulnerabilities
        assert get_color_for_vulnerabilities(0, 0, 0) == BadgeColors.SUCCESS


class TestBadgeCache:
    """Test badge caching functionality."""

    def test_cache_set_get(self):
        """Test basic cache operations."""
        cache = BadgeCache(default_ttl=60)

        # Set value
        cache.set('test/repo', 'coverage', '<svg>test</svg>')

        # Get value
        result = cache.get('test/repo', 'coverage')
        assert result == '<svg>test</svg>'

    def test_cache_expiry(self):
        """Test cache expiration."""
        cache = BadgeCache(default_ttl=0)  # Immediate expiry

        cache.set('test/repo', 'coverage', '<svg>test</svg>')

        # Should expire immediately
        import time
        time.sleep(0.1)
        result = cache.get('test/repo', 'coverage')
        assert result is None

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = BadgeCache()

        # Set multiple badges
        cache.set('test/repo', 'coverage', '<svg>1</svg>')
        cache.set('test/repo', 'quality', '<svg>2</svg>')
        cache.set('other/repo', 'coverage', '<svg>3</svg>')

        # Invalidate specific badge
        count = cache.invalidate('test/repo', 'coverage')
        assert count >= 1

        # Verify invalidation
        assert cache.get('test/repo', 'coverage') is None
        assert cache.get('test/repo', 'quality') is not None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = BadgeCache()
        cache.clear()

        # Add entries
        cache.set('test/repo', 'coverage', '<svg>1</svg>')
        cache.set('test/repo', 'quality', '<svg>2</svg>')

        stats = cache.stats()
        assert stats['total_entries'] == 2
        assert stats['active_entries'] == 2
        assert stats['default_ttl'] == 300


class TestBadgeGenerator:
    """Test badge generation."""

    @pytest.fixture
    def generator(self):
        """Create badge generator with mock cache."""
        cache = BadgeCache()
        cache.clear()
        return BadgeGenerator(cache=cache)

    @pytest.mark.asyncio
    async def test_generate_coverage_badge(self, generator):
        """Test coverage badge generation."""
        svg = await generator.generate_coverage_badge(
            project_id='test/repo',
            coverage_data={'percentage': 85.5},
            style='flat',
        )

        assert '<svg' in svg
        assert '85.5%' in svg
        assert 'coverage' in svg

    @pytest.mark.asyncio
    async def test_generate_quality_badge(self, generator):
        """Test quality badge generation."""
        svg = await generator.generate_quality_badge(
            project_id='test/repo',
            quality_data={'score': 92},
            style='flat',
        )

        assert '<svg' in svg
        assert '92/100' in svg
        assert 'quality' in svg

    @pytest.mark.asyncio
    async def test_generate_security_badge_grade(self, generator):
        """Test security badge with grade."""
        svg = await generator.generate_security_badge(
            project_id='test/repo',
            security_data={'grade': 'A+'},
            style='flat',
        )

        assert '<svg' in svg
        assert 'A+' in svg
        assert 'security' in svg

    @pytest.mark.asyncio
    async def test_generate_security_badge_vulnerabilities(self, generator):
        """Test security badge with vulnerability counts."""
        svg = await generator.generate_security_badge(
            project_id='test/repo',
            security_data={'critical': 2, 'high': 5, 'medium': 10},
            style='flat',
        )

        assert '<svg' in svg
        assert 'critical' in svg
        assert 'security' in svg

    @pytest.mark.asyncio
    async def test_generate_tests_badge(self, generator):
        """Test tests badge generation."""
        svg = await generator.generate_tests_badge(
            project_id='test/repo',
            test_data={'passing': 1234},
            style='flat',
        )

        assert '<svg' in svg
        assert '1,234 passing' in svg
        assert 'tests' in svg

    @pytest.mark.asyncio
    async def test_custom_color(self, generator):
        """Test custom color override."""
        svg = await generator.generate_coverage_badge(
            project_id='test/repo',
            coverage_data={'percentage': 85.5},
            custom_color='#ff0000',
        )

        assert '#ff0000' in svg

    @pytest.mark.asyncio
    async def test_custom_label(self, generator):
        """Test custom label override."""
        svg = await generator.generate_coverage_badge(
            project_id='test/repo',
            coverage_data={'percentage': 85.5},
            custom_label='test cov',
        )

        assert 'test cov' in svg

    @pytest.mark.asyncio
    async def test_badge_caching(self, generator):
        """Test that badges are cached."""
        # Generate badge
        svg1 = await generator.generate_coverage_badge(
            project_id='test/repo',
            coverage_data={'percentage': 85.5},
        )

        # Generate again (should be cached)
        svg2 = await generator.generate_coverage_badge(
            project_id='test/repo',
            coverage_data={'percentage': 85.5},
        )

        assert svg1 == svg2

    @pytest.mark.asyncio
    async def test_different_styles(self, generator):
        """Test different badge styles."""
        styles = ['flat', 'flat-square']

        for style in styles:
            svg = await generator.generate_coverage_badge(
                project_id='test/repo',
                coverage_data={'percentage': 85.5},
                style=style,  # type: ignore
            )
            assert '<svg' in svg

    @pytest.mark.asyncio
    async def test_generate_badge_dispatcher(self, generator):
        """Test badge type dispatcher."""
        # Coverage
        svg = await generator.generate_badge(
            'coverage',
            'test/repo',
            {'percentage': 85.5},
        )
        assert '85.5%' in svg

        # Quality
        svg = await generator.generate_badge(
            'quality',
            'test/repo',
            {'score': 92},
        )
        assert '92/100' in svg

        # Security
        svg = await generator.generate_badge(
            'security',
            'test/repo',
            {'grade': 'A+'},
        )
        assert 'A+' in svg

        # Tests
        svg = await generator.generate_badge(
            'tests',
            'test/repo',
            {'passing': 1234},
        )
        assert '1,234 passing' in svg

    @pytest.mark.asyncio
    async def test_invalid_badge_type(self, generator):
        """Test error handling for invalid badge type."""
        with pytest.raises(ValueError, match="Invalid badge type"):
            await generator.generate_badge(
                'invalid',  # type: ignore
                'test/repo',
                {},
            )

    def test_cache_invalidation(self, generator):
        """Test cache invalidation through generator."""
        # Generate and cache
        import asyncio
        asyncio.run(generator.generate_coverage_badge(
            'test/repo',
            {'percentage': 85.5},
        ))

        # Invalidate
        count = generator.invalidate_cache('test/repo', 'coverage')
        assert count >= 1


class TestBadgeDimensions:
    """Test SVG dimension calculations."""

    @pytest.fixture
    def generator(self):
        return BadgeGenerator()

    def test_dimension_calculation(self, generator):
        """Test dimension calculation for text."""
        dims = generator._calculate_dimensions('coverage', '85.5%', 'flat')

        assert 'width' in dims
        assert 'label_width' in dims
        assert 'message_width' in dims
        assert dims['width'] > 0
        assert dims['label_width'] > 0
        assert dims['message_width'] > 0

    def test_longer_text_dimensions(self, generator):
        """Test dimensions with longer text."""
        dims1 = generator._calculate_dimensions('cov', '85%', 'flat')
        dims2 = generator._calculate_dimensions('coverage', '85.5%', 'flat')

        # Longer text should result in larger dimensions
        assert dims2['width'] > dims1['width']


class TestBadgeRendering:
    """Test SVG rendering."""

    @pytest.fixture
    def generator(self):
        return BadgeGenerator()

    def test_render_badge_flat(self, generator):
        """Test flat style badge rendering."""
        svg = generator._render_badge(
            'test',
            'value',
            '#4c1',
            'flat',
        )

        assert '<svg' in svg
        assert 'test' in svg
        assert 'value' in svg
        assert '#4c1' in svg

    def test_render_badge_flat_square(self, generator):
        """Test flat-square style badge rendering."""
        svg = generator._render_badge(
            'test',
            'value',
            '#4c1',
            'flat-square',
        )

        assert '<svg' in svg
        assert 'shape-rendering="crispEdges"' in svg


# Integration test
class TestBadgeIntegration:
    """Integration tests for complete badge workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete badge generation workflow."""
        # Setup
        cache = BadgeCache()
        generator = BadgeGenerator(cache=cache)

        # Generate all badge types
        badges = {
            'coverage': await generator.generate_coverage_badge(
                'test/repo',
                {'percentage': 85.5},
            ),
            'quality': await generator.generate_quality_badge(
                'test/repo',
                {'score': 92},
            ),
            'security': await generator.generate_security_badge(
                'test/repo',
                {'grade': 'A+'},
            ),
            'tests': await generator.generate_tests_badge(
                'test/repo',
                {'passing': 1234},
            ),
        }

        # Verify all badges generated
        for badge_type, svg in badges.items():
            assert '<svg' in svg
            assert len(svg) > 100

        # Verify caching
        stats = cache.stats()
        assert stats['total_entries'] >= 4

        # Test invalidation
        count = generator.invalidate_cache('test/repo')
        assert count >= 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
