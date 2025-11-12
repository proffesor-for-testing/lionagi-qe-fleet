"""
Edge Case Generator

Comprehensive edge case and corner case generator for testing
robustness and error handling.
"""

import random
import string
from typing import Any, Dict, List

from faker import Faker

fake = Faker()


class EdgeCaseGenerator:
    """Generates comprehensive edge cases"""

    @staticmethod
    def generate_string_edge_cases() -> List[str]:
        """Generate string edge cases"""
        return [
            "",  # Empty
            " ",  # Single space
            "  ",  # Multiple spaces
            "\t",  # Tab
            "\n",  # Newline
            "\r\n",  # Windows newline
            "a",  # Single character
            "x" * 1000,  # Long string
            "x" * 10000,  # Very long string
            "x" * 100000,  # Extremely long string
            "Test\x00Null",  # Null byte
            "Test\u0001Control",  # Control character
            "Ñoño",  # Accented characters
            "日本語",  # Japanese
            "中文",  # Chinese
            "한국어",  # Korean
            "Русский",  # Russian
            "العربية",  # Arabic (RTL)
            "🚀💻🎉",  # Emojis
            "<script>alert('XSS')</script>",  # XSS
            "'; DROP TABLE users; --",  # SQL injection
            "../../../etc/passwd",  # Path traversal
            "Test'Quote",  # Single quote
            'Test"DoubleQuote',  # Double quote
            "Test\\Backslash",  # Backslash
            "Test`Backtick",  # Backtick
            "Test&Ampersand",  # Ampersand
            "Test<Less>Greater",  # Angle brackets
            "".join(chr(i) for i in range(32, 127)),  # All printable ASCII
        ]

    @staticmethod
    def generate_numeric_edge_cases() -> List[Any]:
        """Generate numeric edge cases"""
        return [
            0,
            1,
            -1,
            2147483647,  # Max int32
            -2147483648,  # Min int32
            9223372036854775807,  # Max int64
            -9223372036854775808,  # Min int64
            0.0,
            0.1,
            -0.1,
            float("inf"),
            float("-inf"),
            float("nan"),
            1e-10,  # Very small
            1e10,  # Very large
            3.14159265359,  # Pi
            2.71828182846,  # e
        ]

    @staticmethod
    def generate_array_edge_cases() -> List[List]:
        """Generate array edge cases"""
        return [
            [],  # Empty
            [None],  # Single null
            [1],  # Single item
            list(range(100)),  # Medium array
            list(range(10000)),  # Large array
            [[[]]] * 100,  # Nested arrays
            [None] * 1000,  # All nulls
            [{"nested": {"deep": {"value": i}}} for i in range(10)],  # Deep nesting
        ]

    @staticmethod
    def generate_object_edge_cases() -> List[Dict]:
        """Generate object edge cases"""
        return [
            {},  # Empty
            {"": ""},  # Empty keys and values
            {" ": " "},  # Whitespace keys and values
            {"key": None},  # Null value
            {"null": None, "undefined": None},  # Multiple nulls
            {str(i): i for i in range(1000)},  # Many keys
            {"a": {"b": {"c": {"d": {"e": "value"}}}}},  # Deep nesting
            {f"key{i}": {"nested": {f"key{j}": j for j in range(10)}} for i in range(10)},
        ]

    @staticmethod
    def generate_datetime_edge_cases() -> List[str]:
        """Generate datetime edge cases"""
        return [
            "1970-01-01T00:00:00Z",  # Unix epoch
            "1900-01-01T00:00:00Z",  # Old date
            "2099-12-31T23:59:59Z",  # Future date
            "2000-02-29T12:00:00Z",  # Leap year
            "2001-02-29T12:00:00Z",  # Invalid leap year
            "2025-13-01T00:00:00Z",  # Invalid month
            "2025-01-32T00:00:00Z",  # Invalid day
            "2025-01-01T25:00:00Z",  # Invalid hour
            "2025-01-01T00:60:00Z",  # Invalid minute
            "2025-01-01T00:00:60Z",  # Invalid second
            "invalid-date",  # Completely invalid
            "null",  # Null string
            "",  # Empty string
        ]

    @staticmethod
    def generate_file_path_edge_cases() -> List[str]:
        """Generate file path edge cases"""
        return [
            "",  # Empty
            "/",  # Root
            ".",  # Current dir
            "..",  # Parent dir
            "../../..",  # Multiple parents
            "/etc/passwd",  # System file
            "C:\\Windows\\System32",  # Windows path
            "\\\\network\\share",  # UNC path
            "./valid/path",  # Relative path
            "/absolute/path",  # Absolute path
            "path/with spaces/file.txt",  # Spaces
            "path/with'quotes/file.txt",  # Quotes
            "path/with\"doublequotes/file.txt",  # Double quotes
            "very/long/" + "a/" * 100 + "path",  # Very long path
            "file.txt" + "\x00" + "hidden.txt",  # Null byte injection
        ]

    @staticmethod
    def generate_url_edge_cases() -> List[str]:
        """Generate URL edge cases"""
        return [
            "",  # Empty
            "http://",  # Incomplete
            "https://",  # Incomplete secure
            "http://example.com",  # Simple
            "https://example.com:8080",  # With port
            "https://user:pass@example.com",  # With auth
            "https://example.com/path?query=value",  # With query
            "https://example.com/path#fragment",  # With fragment
            "https://example.com/path?q1=v1&q2=v2#frag",  # Complete
            "ftp://example.com",  # Different protocol
            "javascript:alert('XSS')",  # XSS attempt
            "data:text/html,<script>alert('XSS')</script>",  # Data URL XSS
            "//example.com",  # Protocol-relative
            "http://[::1]:8080",  # IPv6
            "http://192.168.1.1",  # IPv4
        ]

    @staticmethod
    def generate_comprehensive_edge_cases() -> Dict[str, Any]:
        """Generate comprehensive edge case collection"""
        return {
            "strings": EdgeCaseGenerator.generate_string_edge_cases(),
            "numbers": EdgeCaseGenerator.generate_numeric_edge_cases(),
            "arrays": EdgeCaseGenerator.generate_array_edge_cases(),
            "objects": EdgeCaseGenerator.generate_object_edge_cases(),
            "datetimes": EdgeCaseGenerator.generate_datetime_edge_cases(),
            "file_paths": EdgeCaseGenerator.generate_file_path_edge_cases(),
            "urls": EdgeCaseGenerator.generate_url_edge_cases(),
        }
