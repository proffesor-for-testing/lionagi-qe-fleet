"""Compression utilities for artifact storage."""

import gzip
import hashlib
from typing import Tuple


class CompressionUtil:
    """Utilities for compressing and decompressing artifacts."""

    @staticmethod
    def compress(data: bytes, level: int = 6) -> Tuple[bytes, float, str]:
        """
        Compress data using gzip.

        Args:
            data: Raw data to compress
            level: Compression level (1-9, higher = better compression but slower)

        Returns:
            Tuple of (compressed_data, compression_ratio, checksum)
            compression_ratio = compressed_size / original_size (0-1, lower is better)
        """
        if not data:
            return b"", 0.0, hashlib.sha256(b"").hexdigest()

        original_size = len(data)
        compressed_data = gzip.compress(data, compresslevel=level)
        compressed_size = len(compressed_data)
        compression_ratio = compressed_size / original_size if original_size > 0 else 0.0
        checksum = hashlib.sha256(data).hexdigest()

        return compressed_data, compression_ratio, checksum

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """
        Decompress gzip data.

        Args:
            data: Compressed data

        Returns:
            Decompressed data

        Raises:
            ValueError: If data is not valid gzip
        """
        if not data:
            return b""

        try:
            return gzip.decompress(data)
        except Exception as e:
            raise ValueError(f"Failed to decompress data: {e}")

    @staticmethod
    def verify_checksum(data: bytes, expected_checksum: str) -> bool:
        """
        Verify data integrity using SHA-256 checksum.

        Args:
            data: Raw data to verify
            expected_checksum: Expected SHA-256 checksum

        Returns:
            True if checksum matches, False otherwise
        """
        actual_checksum = hashlib.sha256(data).hexdigest()
        return actual_checksum == expected_checksum

    @staticmethod
    def estimate_compressed_size(data: bytes, level: int = 6) -> int:
        """
        Estimate compressed size without actually compressing.
        Uses a small sample for estimation.

        Args:
            data: Data to estimate
            level: Compression level

        Returns:
            Estimated compressed size in bytes
        """
        if not data:
            return 0

        # For small data, just compress it
        if len(data) <= 10000:
            return len(gzip.compress(data, compresslevel=level))

        # For large data, sample 10KB from different parts
        sample_size = 10000
        samples = []
        step = len(data) // 10
        for i in range(0, len(data), step):
            end = min(i + sample_size, len(data))
            samples.append(data[i:end])
            if len(samples) >= 10:
                break

        # Compress samples and calculate average ratio
        total_original = 0
        total_compressed = 0
        for sample in samples:
            total_original += len(sample)
            total_compressed += len(gzip.compress(sample, compresslevel=level))

        avg_ratio = total_compressed / total_original if total_original > 0 else 1.0
        return int(len(data) * avg_ratio)
