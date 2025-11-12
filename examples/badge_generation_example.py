"""
Example: Badge generation service usage.

Demonstrates how to generate badges programmatically.
"""

import asyncio
from pathlib import Path

from lionagi_qe.badges.generator import BadgeGenerator
from lionagi_qe.badges.cache import BadgeCache


async def main():
    """Generate example badges."""
    # Initialize generator with cache
    cache = BadgeCache(default_ttl=300)  # 5 minutes
    generator = BadgeGenerator(cache=cache)

    output_dir = Path('examples/badges')
    output_dir.mkdir(exist_ok=True)

    print("\n🎨 Badge Generation Examples\n")
    print("=" * 50)

    # 1. Coverage Badge
    print("\n1. Coverage Badge (85.5%)")
    coverage_svg = await generator.generate_coverage_badge(
        project_id='lionagi/qe-fleet',
        coverage_data={'percentage': 85.5},
        style='flat',
    )
    output_file = output_dir / 'badge-coverage.svg'
    output_file.write_text(coverage_svg)
    print(f"   ✓ Saved to: {output_file}")

    # 2. Quality Badge
    print("\n2. Quality Badge (92/100)")
    quality_svg = await generator.generate_quality_badge(
        project_id='lionagi/qe-fleet',
        quality_data={'score': 92},
        style='flat',
    )
    output_file = output_dir / 'badge-quality.svg'
    output_file.write_text(quality_svg)
    print(f"   ✓ Saved to: {output_file}")

    # 3. Security Badge (Grade)
    print("\n3. Security Badge (A+ Grade)")
    security_svg = await generator.generate_security_badge(
        project_id='lionagi/qe-fleet',
        security_data={'grade': 'A+'},
        style='flat',
    )
    output_file = output_dir / 'badge-security-grade.svg'
    output_file.write_text(security_svg)
    print(f"   ✓ Saved to: {output_file}")

    # 4. Security Badge (Vulnerabilities)
    print("\n4. Security Badge (2 Critical)")
    security_vuln_svg = await generator.generate_security_badge(
        project_id='lionagi/qe-fleet',
        security_data={'critical': 2, 'high': 5, 'medium': 10},
        style='flat',
    )
    output_file = output_dir / 'badge-security-vuln.svg'
    output_file.write_text(security_vuln_svg)
    print(f"   ✓ Saved to: {output_file}")

    # 5. Tests Badge
    print("\n5. Tests Badge (1,234 Passing)")
    tests_svg = await generator.generate_tests_badge(
        project_id='lionagi/qe-fleet',
        test_data={'passing': 1234},
        style='flat',
    )
    output_file = output_dir / 'badge-tests.svg'
    output_file.write_text(tests_svg)
    print(f"   ✓ Saved to: {output_file}")

    # 6. Custom Styling Examples
    print("\n6. Custom Styling Examples")

    # Flat-square style
    coverage_flat_square = await generator.generate_coverage_badge(
        project_id='lionagi/qe-fleet',
        coverage_data={'percentage': 85.5},
        style='flat-square',
    )
    output_file = output_dir / 'badge-coverage-flat-square.svg'
    output_file.write_text(coverage_flat_square)
    print(f"   ✓ Flat-square: {output_file}")

    # Custom color
    coverage_custom_color = await generator.generate_coverage_badge(
        project_id='lionagi/qe-fleet',
        coverage_data={'percentage': 85.5},
        custom_color='#ff6b6b',
    )
    output_file = output_dir / 'badge-coverage-custom-color.svg'
    output_file.write_text(coverage_custom_color)
    print(f"   ✓ Custom color: {output_file}")

    # Custom label
    coverage_custom_label = await generator.generate_coverage_badge(
        project_id='lionagi/qe-fleet',
        coverage_data={'percentage': 85.5},
        custom_label='test cov',
    )
    output_file = output_dir / 'badge-coverage-custom-label.svg'
    output_file.write_text(coverage_custom_label)
    print(f"   ✓ Custom label: {output_file}")

    # 7. Cache Statistics
    print("\n7. Cache Statistics")
    stats = cache.stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Active entries: {stats['active_entries']}")
    print(f"   Default TTL: {stats['default_ttl']}s")

    # 8. Cache Invalidation
    print("\n8. Cache Invalidation")
    count = generator.invalidate_cache('lionagi/qe-fleet', 'coverage')
    print(f"   ✓ Invalidated {count} coverage badge(s)")

    print("\n" + "=" * 50)
    print("✓ Badge generation complete!")
    print(f"\nView badges in: {output_dir.absolute()}")
    print("\nIntegration examples:")
    print("  Markdown: ![Coverage](https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet)")
    print("  HTML:     <img src='https://api.lionagi-qe.io/badge/coverage/lionagi/qe-fleet'>")


if __name__ == '__main__':
    asyncio.run(main())
