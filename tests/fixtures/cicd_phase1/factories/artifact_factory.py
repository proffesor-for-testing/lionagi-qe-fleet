"""
Artifact Factories

Generates various artifact types (JSON, XML, binary) for testing
artifact storage, retrieval, and processing in CI/CD pipelines.
"""

import base64
import json
import random
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

from faker import Faker

fake = Faker()


class ArtifactFactory:
    """Base factory for CI/CD artifacts"""

    @staticmethod
    def create_metadata(artifact_type: str = "generic") -> Dict[str, Any]:
        """Generate artifact metadata"""
        return {
            "artifact_id": str(uuid.uuid4()),
            "name": f"{artifact_type}-{fake.slug()}",
            "type": artifact_type,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": fake.user_name(),
            "build_id": str(uuid.uuid4()),
            "pipeline": {
                "id": str(uuid.uuid4()),
                "name": fake.job(),
                "stage": random.choice(["build", "test", "deploy"]),
            },
            "retention": {
                "days": random.randint(1, 90),
                "expires_at": (datetime.utcnow().timestamp() + random.randint(86400, 7776000)),
            },
            "tags": [fake.word() for _ in range(random.randint(1, 5))],
        }


class JSONArtifactFactory(ArtifactFactory):
    """Factory for JSON artifacts"""

    @staticmethod
    def create_test_results(
        total_tests: int = 100,
        pass_rate: float = 0.85,
    ) -> Dict[str, Any]:
        """Generate test results JSON artifact"""
        passed = int(total_tests * pass_rate)
        failed = int(total_tests * (1 - pass_rate) * 0.7)
        skipped = total_tests - passed - failed

        tests = []
        for i in range(total_tests):
            status = "passed"
            if i >= passed:
                status = "failed" if i < (passed + failed) else "skipped"

            test = {
                "id": str(uuid.uuid4()),
                "name": f"test_{fake.slug()}",
                "status": status,
                "duration": random.uniform(0.001, 5.0),
                "suite": random.choice(["unit", "integration", "e2e"]),
            }

            if status == "failed":
                test["error"] = {
                    "type": random.choice(["AssertionError", "ValueError", "RuntimeError"]),
                    "message": fake.sentence(),
                    "traceback": "\n".join([f"  File {fake.file_path()}, line {random.randint(1, 100)}" for _ in range(3)]),
                }

            tests.append(test)

        return {
            **JSONArtifactFactory.create_metadata("test-results"),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": passed / total_tests,
                "duration": sum(t["duration"] for t in tests),
            },
            "tests": tests,
        }

    @staticmethod
    def create_coverage_report(
        line_coverage: float = 0.85,
        branch_coverage: float = 0.75,
    ) -> Dict[str, Any]:
        """Generate coverage report JSON artifact"""
        files = []
        for _ in range(random.randint(10, 50)):
            file_lines = random.randint(50, 500)
            covered_lines = int(file_lines * random.uniform(line_coverage - 0.1, line_coverage + 0.1))

            files.append({
                "path": f"src/{fake.file_path(extension='py')}",
                "lines": {
                    "total": file_lines,
                    "covered": covered_lines,
                    "missed": file_lines - covered_lines,
                    "percentage": (covered_lines / file_lines) * 100,
                },
                "branches": {
                    "total": random.randint(10, 50),
                    "covered": int(random.randint(10, 50) * random.uniform(branch_coverage - 0.1, branch_coverage + 0.1)),
                },
            })

        total_lines = sum(f["lines"]["total"] for f in files)
        covered_lines = sum(f["lines"]["covered"] for f in files)

        return {
            **JSONArtifactFactory.create_metadata("coverage-report"),
            "summary": {
                "line_coverage": (covered_lines / total_lines) * 100,
                "branch_coverage": branch_coverage * 100,
                "lines": {
                    "total": total_lines,
                    "covered": covered_lines,
                    "missed": total_lines - covered_lines,
                },
            },
            "files": files,
        }

    @staticmethod
    def create_build_manifest() -> Dict[str, Any]:
        """Generate build manifest JSON artifact"""
        return {
            **JSONArtifactFactory.create_metadata("build-manifest"),
            "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 100)}",
            "commit": fake.sha256()[:40],
            "branch": random.choice(["main", "develop", "release/v1.0"]),
            "artifacts": [
                {
                    "name": fake.file_name(extension=ext),
                    "type": ext,
                    "size_bytes": random.randint(1024, 10485760),
                    "checksum": fake.sha256(),
                }
                for ext in ["whl", "tar.gz", "zip"]
            ],
            "dependencies": [
                {
                    "name": fake.word(),
                    "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 10)}",
                    "type": random.choice(["runtime", "dev", "test"]),
                }
                for _ in range(random.randint(10, 30))
            ],
        }


class XMLArtifactFactory(ArtifactFactory):
    """Factory for XML artifacts"""

    @staticmethod
    def create_junit_xml(
        total_tests: int = 100,
        pass_rate: float = 0.85,
    ) -> str:
        """Generate JUnit XML test results"""
        passed = int(total_tests * pass_rate)
        failed = total_tests - passed

        testsuites = ET.Element("testsuites", {
            "tests": str(total_tests),
            "failures": str(failed),
            "time": str(random.uniform(10.0, 300.0)),
        })

        for suite_idx in range(random.randint(3, 10)):
            suite_tests = random.randint(5, 20)
            suite_failures = int(suite_tests * (1 - pass_rate))

            testsuite = ET.SubElement(testsuites, "testsuite", {
                "name": f"TestSuite{suite_idx}",
                "tests": str(suite_tests),
                "failures": str(suite_failures),
                "time": str(random.uniform(1.0, 30.0)),
            })

            for test_idx in range(suite_tests):
                testcase = ET.SubElement(testsuite, "testcase", {
                    "name": f"test_{fake.slug()}",
                    "classname": f"test_{fake.slug()}",
                    "time": str(random.uniform(0.001, 5.0)),
                })

                if test_idx < suite_failures:
                    failure = ET.SubElement(testcase, "failure", {
                        "message": fake.sentence(),
                        "type": "AssertionError",
                    })
                    failure.text = fake.text()

        return ET.tostring(testsuites, encoding="unicode")

    @staticmethod
    def create_checkstyle_xml(file_count: int = 20) -> str:
        """Generate Checkstyle XML report"""
        checkstyle = ET.Element("checkstyle", {"version": "10.0"})

        for _ in range(file_count):
            file_elem = ET.SubElement(checkstyle, "file", {
                "name": f"src/{fake.file_path(extension='py')}",
            })

            for _ in range(random.randint(0, 10)):
                ET.SubElement(file_elem, "error", {
                    "line": str(random.randint(1, 500)),
                    "column": str(random.randint(1, 80)),
                    "severity": random.choice(["error", "warning", "info"]),
                    "message": fake.sentence(),
                    "source": f"checkstyle.{fake.word()}",
                })

        return ET.tostring(checkstyle, encoding="unicode")


class BinaryArtifactFactory(ArtifactFactory):
    """Factory for binary artifacts"""

    @staticmethod
    def create_tarball(size_kb: int = 1024) -> bytes:
        """Generate mock tarball (base64 encoded for testing)"""
        # Mock tarball header + random data
        mock_data = b"PK\x03\x04" + bytes(random.getrandbits(8) for _ in range(size_kb * 1024))
        return mock_data

    @staticmethod
    def create_zip_archive(size_kb: int = 512) -> bytes:
        """Generate mock ZIP archive"""
        # Mock ZIP header + random data
        mock_data = b"\x50\x4b\x03\x04" + bytes(random.getrandbits(8) for _ in range(size_kb * 1024))
        return mock_data

    @staticmethod
    def create_image(width: int = 800, height: int = 600) -> bytes:
        """Generate mock PNG image"""
        # Mock PNG header + random data
        png_header = b"\x89PNG\r\n\x1a\n"
        mock_data = png_header + bytes(random.getrandbits(8) for _ in range(width * height // 10))
        return mock_data

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """Encode binary data as base64"""
        return base64.b64encode(data).decode("utf-8")


# Edge case artifacts
class EdgeCaseArtifactFactory:
    """Factory for edge case artifacts"""

    @staticmethod
    def create_empty_json() -> Dict[str, Any]:
        """Generate empty JSON artifact"""
        return {}

    @staticmethod
    def create_corrupted_json() -> str:
        """Generate corrupted JSON string"""
        return '{"tests": [{"name": "test1", "status": "passed"'  # Missing closing brackets

    @staticmethod
    def create_oversized_artifact(size_mb: float = 100.0) -> Dict[str, Any]:
        """Generate oversized artifact"""
        return {
            "artifact_id": str(uuid.uuid4()),
            "data": "x" * int(size_mb * 1024 * 1024),
        }

    @staticmethod
    def create_nested_artifact(depth: int = 50) -> Dict[str, Any]:
        """Generate deeply nested artifact"""
        result = {"level": depth}
        current = result
        for i in range(depth - 1, 0, -1):
            current["nested"] = {"level": i}
            current = current["nested"]
        return result

    @staticmethod
    def create_unicode_artifact() -> Dict[str, Any]:
        """Generate artifact with unicode characters"""
        return {
            "artifact_id": str(uuid.uuid4()),
            "test_names": [
                "test_日本語",
                "test_中文",
                "test_한국어",
                "test_Русский",
                "test_العربية",
                "test_🚀💻",
            ],
            "messages": [
                "Test with emoji: 🎉✅❌",
                "Test with accents: Ñoño",
                "Test with RTL: مرحبا",
            ],
        }
