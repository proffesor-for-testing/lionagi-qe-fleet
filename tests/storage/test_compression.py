"""Tests for compression utilities."""

import pytest
from lionagi_qe.storage.utils.compression import CompressionUtil


class TestCompressionUtil:
    """Test compression utilities."""

    def test_compress_empty_data(self):
        """Test compressing empty data."""
        compressed, ratio, checksum = CompressionUtil.compress(b"")
        assert compressed == b""
        assert ratio == 0.0
        assert len(checksum) == 64  # SHA-256 hex

    def test_compress_small_data(self):
        """Test compressing small data."""
        data = b"Hello, World!" * 10
        compressed, ratio, checksum = CompressionUtil.compress(data)

        assert len(compressed) > 0
        assert len(compressed) < len(data)  # Should be compressed
        assert 0 < ratio < 1  # Ratio should be between 0 and 1
        assert len(checksum) == 64

    def test_compress_large_data(self):
        """Test compressing large data."""
        data = b"A" * 100000  # 100KB of 'A'
        compressed, ratio, checksum = CompressionUtil.compress(data, level=9)

        assert len(compressed) > 0
        assert len(compressed) < len(data)
        assert ratio < 0.01  # Should compress very well (repeated data)

    def test_compress_random_data(self):
        """Test compressing random data (not very compressible)."""
        import random

        data = bytes(random.getrandbits(8) for _ in range(10000))
        compressed, ratio, checksum = CompressionUtil.compress(data)

        # Random data doesn't compress well
        assert ratio > 0.9  # Ratio close to 1

    def test_decompress(self):
        """Test decompression."""
        original = b"Test data " * 1000
        compressed, _, _ = CompressionUtil.compress(original)
        decompressed = CompressionUtil.decompress(compressed)

        assert decompressed == original

    def test_decompress_empty(self):
        """Test decompressing empty data."""
        decompressed = CompressionUtil.decompress(b"")
        assert decompressed == b""

    def test_decompress_invalid_data(self):
        """Test decompressing invalid data."""
        with pytest.raises(ValueError, match="Failed to decompress"):
            CompressionUtil.decompress(b"invalid gzip data")

    def test_verify_checksum_valid(self):
        """Test checksum verification with valid checksum."""
        data = b"Test data"
        _, _, checksum = CompressionUtil.compress(data)

        assert CompressionUtil.verify_checksum(data, checksum)

    def test_verify_checksum_invalid(self):
        """Test checksum verification with invalid checksum."""
        data = b"Test data"
        wrong_checksum = "0" * 64

        assert not CompressionUtil.verify_checksum(data, wrong_checksum)

    def test_compression_levels(self):
        """Test different compression levels."""
        data = b"Test " * 10000
        results = {}

        for level in range(1, 10):
            compressed, ratio, _ = CompressionUtil.compress(data, level)
            results[level] = (len(compressed), ratio)

        # Higher levels should generally produce smaller output
        # (though not always guaranteed for all data)
        assert results[9][1] <= results[1][1]

    def test_estimate_compressed_size_small(self):
        """Test size estimation for small data."""
        data = b"A" * 5000
        estimated = CompressionUtil.estimate_compressed_size(data)
        compressed, _, _ = CompressionUtil.compress(data)

        # Estimate should be within 50% of actual
        assert 0.5 * len(compressed) <= estimated <= 1.5 * len(compressed)

    def test_estimate_compressed_size_large(self):
        """Test size estimation for large data."""
        data = b"B" * 1000000  # 1MB
        estimated = CompressionUtil.estimate_compressed_size(data)

        # For large repeated data, estimate should be reasonable
        assert estimated < len(data)
        assert estimated > 0

    def test_estimate_compressed_size_empty(self):
        """Test size estimation for empty data."""
        estimated = CompressionUtil.estimate_compressed_size(b"")
        assert estimated == 0

    def test_round_trip(self):
        """Test full compress-decompress round trip."""
        test_cases = [
            b"",
            b"x",
            b"Hello, World!",
            b"A" * 10000,
            b"Mixed content: " + bytes(range(256)),
        ]

        for original in test_cases:
            compressed, _, checksum = CompressionUtil.compress(original)
            decompressed = CompressionUtil.decompress(compressed)

            assert decompressed == original
            assert CompressionUtil.verify_checksum(original, checksum)
