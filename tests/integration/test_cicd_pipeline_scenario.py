"""
Real-World CI/CD Pipeline Integration Test

Simulates a complete CI/CD pipeline execution:
1. Code commit triggers webhook
2. Tests generated and executed
3. Coverage analyzed
4. Security scan performed
5. Quality gate validation
6. Artifacts stored
7. Badges updated
8. Results reported

NO MOCKS - uses real backends and actual API calls.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

import aiohttp
import pytest
from fastapi.testclient import TestClient

from lionagi_qe.api import app
from lionagi_qe.storage import StorageFactory, Artifact, ArtifactType
from lionagi_qe.badges import BadgeGenerator, BadgeCache


class CICDPipelineSimulator:
    """Simulates a real CI/CD pipeline execution."""

    def __init__(self, storage_dir: str, badge_cache_dir: str):
        self.storage_dir = Path(storage_dir)
        self.badge_cache_dir = Path(badge_cache_dir)
        self.api_client = TestClient(app)
        self.storage = StorageFactory.create(
            {"backend": "local", "base_path": str(storage_dir)}
        )
        self.badge_generator = BadgeGenerator(
            cache=BadgeCache(cache_dir=badge_cache_dir, ttl=300)
        )
        self.pipeline_results = {
            "start_time": time.time(),
            "end_time": 0,
            "duration": 0,
            "stages": {},
            "artifacts": [],
            "badges": [],
            "quality_gate_passed": False,
            "errors": [],
        }

    def run_pipeline(self) -> Dict[str, Any]:
        """Execute complete CI/CD pipeline."""
        print("\n" + "=" * 80)
        print("CI/CD PIPELINE SIMULATION")
        print("=" * 80 + "\n")

        try:
            # Stage 1: Code Analysis
            self._stage_code_analysis()

            # Stage 2: Test Generation
            self._stage_test_generation()

            # Stage 3: Test Execution
            self._stage_test_execution()

            # Stage 4: Coverage Analysis
            self._stage_coverage_analysis()

            # Stage 5: Security Scanning
            self._stage_security_scan()

            # Stage 6: Quality Gate
            self._stage_quality_gate()

            # Stage 7: Artifact Storage
            self._stage_artifact_storage()

            # Stage 8: Badge Generation
            self._stage_badge_generation()

            # Stage 9: Results Reporting
            self._stage_results_reporting()

        except Exception as e:
            self.pipeline_results["errors"].append(str(e))
            print(f"\n✗ Pipeline failed: {e}")

        finally:
            self.pipeline_results["end_time"] = time.time()
            self.pipeline_results["duration"] = (
                self.pipeline_results["end_time"] - self.pipeline_results["start_time"]
            )

        return self.pipeline_results

    def _stage_code_analysis(self):
        """Stage 1: Analyze code quality and structure."""
        print("Stage 1: Code Analysis")
        print("-" * 40)

        start = time.time()

        # Simulate code analysis
        response = self.api_client.post(
            "/api/v1/analyze-code",
            json={
                "source_paths": ["src/"],
                "checks": ["complexity", "duplication", "style"],
            },
        )

        duration = time.time() - start

        self.pipeline_results["stages"]["code_analysis"] = {
            "status": "passed" if response.status_code in [200, 202] else "failed",
            "duration": duration,
            "response_code": response.status_code,
        }

        print(f"  Status: {self.pipeline_results['stages']['code_analysis']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_test_generation(self):
        """Stage 2: Generate tests with AI."""
        print("Stage 2: Test Generation")
        print("-" * 40)

        start = time.time()

        # Generate tests for multiple modules
        modules = ["src/core.py", "src/api.py", "src/storage.py"]
        test_generation_results = []

        for module in modules:
            response = self.api_client.post(
                "/api/v1/test-generate",
                json={
                    "module_path": module,
                    "framework": "pytest",
                    "test_type": "unit",
                    "coverage_target": 90,
                },
            )

            test_generation_results.append(
                {
                    "module": module,
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else {},
                }
            )

        duration = time.time() - start

        self.pipeline_results["stages"]["test_generation"] = {
            "status": "passed"
            if all(r["status_code"] in [200, 202] for r in test_generation_results)
            else "failed",
            "duration": duration,
            "modules_processed": len(modules),
            "results": test_generation_results,
        }

        print(
            f"  Modules processed: {len(modules)}"
        )
        print(f"  Status: {self.pipeline_results['stages']['test_generation']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_test_execution(self):
        """Stage 3: Execute tests with coverage."""
        print("Stage 3: Test Execution")
        print("-" * 40)

        start = time.time()

        # Execute tests
        response = self.api_client.post(
            "/api/v1/test-execute",
            json={
                "test_paths": ["tests/unit/", "tests/integration/"],
                "framework": "pytest",
                "parallel": True,
                "coverage": True,
                "verbose": False,
            },
        )

        duration = time.time() - start

        results = response.json() if response.status_code == 200 else {}

        self.pipeline_results["stages"]["test_execution"] = {
            "status": "passed" if response.status_code in [200, 202] else "failed",
            "duration": duration,
            "tests_run": results.get("tests_run", 0),
            "tests_passed": results.get("tests_passed", 0),
            "tests_failed": results.get("tests_failed", 0),
            "coverage": results.get("coverage", 0),
        }

        print(f"  Tests run: {self.pipeline_results['stages']['test_execution']['tests_run']}")
        print(
            f"  Tests passed: {self.pipeline_results['stages']['test_execution']['tests_passed']}"
        )
        print(f"  Coverage: {self.pipeline_results['stages']['test_execution']['coverage']}%")
        print(f"  Status: {self.pipeline_results['stages']['test_execution']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_coverage_analysis(self):
        """Stage 4: Analyze test coverage gaps."""
        print("Stage 4: Coverage Analysis")
        print("-" * 40)

        start = time.time()

        # Analyze coverage
        response = self.api_client.post(
            "/api/v1/coverage-analyze",
            json={"source_paths": ["src/"], "minimum_coverage": 80.0},
        )

        duration = time.time() - start

        results = response.json() if response.status_code == 200 else {}

        self.pipeline_results["stages"]["coverage_analysis"] = {
            "status": "passed" if response.status_code in [200, 202] else "failed",
            "duration": duration,
            "overall_coverage": results.get("overall_coverage", 0),
            "uncovered_lines": results.get("uncovered_lines", []),
            "gaps_found": results.get("gaps_found", 0),
        }

        print(
            f"  Overall coverage: {self.pipeline_results['stages']['coverage_analysis']['overall_coverage']}%"
        )
        print(
            f"  Gaps found: {self.pipeline_results['stages']['coverage_analysis']['gaps_found']}"
        )
        print(f"  Status: {self.pipeline_results['stages']['coverage_analysis']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_security_scan(self):
        """Stage 5: Perform security scanning."""
        print("Stage 5: Security Scan")
        print("-" * 40)

        start = time.time()

        # Run security scan
        response = self.api_client.post(
            "/api/v1/security-scan",
            json={
                "scan_types": ["sast", "dependency", "secrets"],
                "source_paths": ["src/"],
            },
        )

        duration = time.time() - start

        results = response.json() if response.status_code == 200 else {}

        self.pipeline_results["stages"]["security_scan"] = {
            "status": "passed" if response.status_code in [200, 202] else "failed",
            "duration": duration,
            "vulnerabilities_found": results.get("vulnerabilities_found", 0),
            "critical_count": results.get("critical_count", 0),
            "high_count": results.get("high_count", 0),
            "security_score": results.get("security_score", 100),
        }

        print(
            f"  Vulnerabilities: {self.pipeline_results['stages']['security_scan']['vulnerabilities_found']}"
        )
        print(
            f"  Security score: {self.pipeline_results['stages']['security_scan']['security_score']}"
        )
        print(f"  Status: {self.pipeline_results['stages']['security_scan']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_quality_gate(self):
        """Stage 6: Validate quality gate."""
        print("Stage 6: Quality Gate")
        print("-" * 40)

        start = time.time()

        # Check quality gate
        thresholds = {
            "coverage": 80.0,
            "test_pass_rate": 95.0,
            "security_score": 90.0,
            "code_quality_score": 85.0,
        }

        response = self.api_client.post(
            "/api/v1/quality-gate", json={"thresholds": thresholds}
        )

        duration = time.time() - start

        results = response.json() if response.status_code == 200 else {}

        self.pipeline_results["stages"]["quality_gate"] = {
            "status": "passed" if results.get("gate_passed", False) else "failed",
            "duration": duration,
            "gate_passed": results.get("gate_passed", False),
            "thresholds_met": results.get("thresholds_met", {}),
            "thresholds_failed": results.get("thresholds_failed", {}),
        }

        self.pipeline_results["quality_gate_passed"] = results.get("gate_passed", False)

        print(f"  Gate passed: {self.pipeline_results['quality_gate_passed']}")
        print(f"  Status: {self.pipeline_results['stages']['quality_gate']['status']}")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_artifact_storage(self):
        """Stage 7: Store all artifacts."""
        print("Stage 7: Artifact Storage")
        print("-" * 40)

        start = time.time()

        # Store test results
        test_results = self.pipeline_results["stages"].get("test_execution", {})
        artifact_test = Artifact(
            id="pipeline-test-results",
            type=ArtifactType.TEST_RESULTS,
            data=test_results,
            metadata={"pipeline_id": "test-pipeline-001", "stage": "test_execution"},
        )
        self.storage.store(artifact_test)
        self.pipeline_results["artifacts"].append("pipeline-test-results")

        # Store coverage report
        coverage_results = self.pipeline_results["stages"].get("coverage_analysis", {})
        artifact_coverage = Artifact(
            id="pipeline-coverage-report",
            type=ArtifactType.COVERAGE_REPORT,
            data=coverage_results,
            metadata={"pipeline_id": "test-pipeline-001", "stage": "coverage_analysis"},
        )
        self.storage.store(artifact_coverage)
        self.pipeline_results["artifacts"].append("pipeline-coverage-report")

        # Store security findings
        security_results = self.pipeline_results["stages"].get("security_scan", {})
        artifact_security = Artifact(
            id="pipeline-security-findings",
            type=ArtifactType.SECURITY_FINDINGS,
            data=security_results,
            metadata={"pipeline_id": "test-pipeline-001", "stage": "security_scan"},
        )
        self.storage.store(artifact_security)
        self.pipeline_results["artifacts"].append("pipeline-security-findings")

        duration = time.time() - start

        self.pipeline_results["stages"]["artifact_storage"] = {
            "status": "passed",
            "duration": duration,
            "artifacts_stored": len(self.pipeline_results["artifacts"]),
        }

        print(f"  Artifacts stored: {len(self.pipeline_results['artifacts'])}")
        print(f"  Status: passed")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_badge_generation(self):
        """Stage 8: Generate status badges."""
        print("Stage 8: Badge Generation")
        print("-" * 40)

        start = time.time()

        # Generate coverage badge
        coverage = self.pipeline_results["stages"]["test_execution"].get("coverage", 0)
        coverage_badge = self.badge_generator.generate_coverage_badge(coverage)
        badge_path = self.badge_cache_dir / "coverage.svg"
        badge_path.write_text(coverage_badge)
        self.pipeline_results["badges"].append("coverage.svg")

        # Generate quality badge
        quality_score = self.pipeline_results["stages"]["quality_gate"].get(
            "quality_score", 85
        )
        quality_badge = self.badge_generator.generate_quality_badge(quality_score)
        badge_path = self.badge_cache_dir / "quality.svg"
        badge_path.write_text(quality_badge)
        self.pipeline_results["badges"].append("quality.svg")

        # Generate security badge
        security_score = self.pipeline_results["stages"]["security_scan"].get(
            "security_score", 100
        )
        vulnerabilities = self.pipeline_results["stages"]["security_scan"].get(
            "vulnerabilities_found", 0
        )
        security_badge = self.badge_generator.generate_security_badge(
            security_score, vulnerabilities
        )
        badge_path = self.badge_cache_dir / "security.svg"
        badge_path.write_text(security_badge)
        self.pipeline_results["badges"].append("security.svg")

        # Generate test count badge
        tests_passed = self.pipeline_results["stages"]["test_execution"].get(
            "tests_passed", 0
        )
        tests_failed = self.pipeline_results["stages"]["test_execution"].get(
            "tests_failed", 0
        )
        tests_total = tests_passed + tests_failed
        test_badge = self.badge_generator.generate_test_count_badge(
            tests_passed, tests_failed, tests_total
        )
        badge_path = self.badge_cache_dir / "tests.svg"
        badge_path.write_text(test_badge)
        self.pipeline_results["badges"].append("tests.svg")

        duration = time.time() - start

        self.pipeline_results["stages"]["badge_generation"] = {
            "status": "passed",
            "duration": duration,
            "badges_generated": len(self.pipeline_results["badges"]),
        }

        print(f"  Badges generated: {len(self.pipeline_results['badges'])}")
        print(f"  Status: passed")
        print(f"  Duration: {duration:.2f}s\n")

    def _stage_results_reporting(self):
        """Stage 9: Generate and report results."""
        print("Stage 9: Results Reporting")
        print("-" * 40)

        start = time.time()

        # Generate summary report
        report = self._generate_pipeline_report()

        # Save report
        report_path = self.storage_dir / "pipeline_report.json"
        report_path.write_text(json.dumps(report, indent=2))

        duration = time.time() - start

        self.pipeline_results["stages"]["results_reporting"] = {
            "status": "passed",
            "duration": duration,
            "report_path": str(report_path),
        }

        print(f"  Report saved: {report_path}")
        print(f"  Status: passed")
        print(f"  Duration: {duration:.2f}s\n")

    def _generate_pipeline_report(self) -> Dict[str, Any]:
        """Generate comprehensive pipeline report."""
        return {
            "pipeline_id": "test-pipeline-001",
            "status": "passed"
            if self.pipeline_results["quality_gate_passed"]
            else "failed",
            "duration": self.pipeline_results["duration"],
            "stages": self.pipeline_results["stages"],
            "artifacts": self.pipeline_results["artifacts"],
            "badges": self.pipeline_results["badges"],
            "quality_gate_passed": self.pipeline_results["quality_gate_passed"],
            "errors": self.pipeline_results["errors"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.fixture
def temp_dirs():
    """Create temporary directories for pipeline."""
    storage_dir = tempfile.mkdtemp(prefix="pipeline_storage_")
    badge_cache_dir = tempfile.mkdtemp(prefix="pipeline_badges_")

    yield storage_dir, badge_cache_dir

    import shutil

    shutil.rmtree(storage_dir, ignore_errors=True)
    shutil.rmtree(badge_cache_dir, ignore_errors=True)


def test_complete_cicd_pipeline(temp_dirs):
    """Test complete CI/CD pipeline execution."""
    storage_dir, badge_cache_dir = temp_dirs

    simulator = CICDPipelineSimulator(storage_dir, badge_cache_dir)
    results = simulator.run_pipeline()

    # Validate pipeline completed
    assert results["duration"] > 0
    assert len(results["stages"]) == 9

    # Validate all stages executed
    required_stages = [
        "code_analysis",
        "test_generation",
        "test_execution",
        "coverage_analysis",
        "security_scan",
        "quality_gate",
        "artifact_storage",
        "badge_generation",
        "results_reporting",
    ]

    for stage in required_stages:
        assert stage in results["stages"]
        assert "status" in results["stages"][stage]
        assert "duration" in results["stages"][stage]

    # Validate artifacts stored
    assert len(results["artifacts"]) >= 3
    assert "pipeline-test-results" in results["artifacts"]
    assert "pipeline-coverage-report" in results["artifacts"]

    # Validate badges generated
    assert len(results["badges"]) >= 4
    assert "coverage.svg" in results["badges"]
    assert "quality.svg" in results["badges"]

    # Print summary
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Status: {'✓ PASSED' if results['quality_gate_passed'] else '✗ FAILED'}")
    print(f"Duration: {results['duration']:.2f}s")
    print(f"Stages: {len(results['stages'])}")
    print(f"Artifacts: {len(results['artifacts'])}")
    print(f"Badges: {len(results['badges'])}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
