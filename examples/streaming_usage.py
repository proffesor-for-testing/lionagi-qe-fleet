"""
Example usage of streaming progress updates in QE agents

This file demonstrates practical usage patterns for streaming functionality
in the Agentic QE Fleet.
"""

import asyncio
from typing import Dict, Any


# Example 1: Test Generation with Progress Tracking
async def example_test_generation_streaming():
    """Example: Generate tests with real-time progress"""
    from lionagi_qe.agents.test_generator import TestGeneratorAgent
    from lionagi_qe.core.task import QETask

    # Note: In production, agent would be initialized via QEFleet
    # This is a conceptual example showing the API

    print("\n" + "="*80)
    print("EXAMPLE 1: Test Generation with Streaming")
    print("="*80 + "\n")

    # Create task for test generation
    task = QETask(
        task_type="test_generation",
        context={
            "code": """
def calculate_discount(price: float, discount_percent: float) -> float:
    '''Calculate discounted price'''
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)
""",
            "framework": "pytest",
            "test_type": "unit",
            "coverage_target": 90,
            "target_count": 10,
        }
    )

    # Simulate streaming (in production, use actual agent)
    print("Task: Generate 10 unit tests for calculate_discount()")
    print("-" * 80)

    # Track progress
    tests_generated = []

    # Stream test generation
    # async for event in agent.generate_tests_streaming(task):
    #     if event["type"] == "progress":
    #         # Show progress bar
    #         percent = event["percent"]
    #         bar_length = 40
    #         filled = int(bar_length * percent / 100)
    #         bar = "█" * filled + "░" * (bar_length - filled)
    #         print(f"\r[{bar}] {percent:.1f}% - {event['message']}", end="", flush=True)
    #
    #     elif event["type"] == "test":
    #         print()  # New line after progress
    #         test_case = event["test_case"]
    #         tests_generated.append(test_case)
    #         print(f"✓ Generated: {test_case['test_name']}")
    #         print(f"  Coverage estimate: {test_case['coverage_estimate']}%")
    #
    #     elif event["type"] == "complete":
    #         print()  # New line
    #         print("-" * 80)
    #         print(f"✅ Complete! Generated {event['total']} tests")
    #         print(f"📊 Average coverage: {event['coverage_estimate']}%")
    #         print(f"🎯 Framework: {event['framework']}")

    print("\nAPI Usage Pattern:")
    print("""
    async for event in agent.generate_tests_streaming(task):
        if event["type"] == "progress":
            update_progress_bar(event["percent"], event["message"])

        elif event["type"] == "test":
            display_test(event["test_case"])

        elif event["type"] == "complete":
            display_summary(event["tests"], event["coverage_estimate"])
    """)


# Example 2: Coverage Analysis with Real-Time Alerts
async def example_coverage_analysis_streaming():
    """Example: Analyze coverage with real-time gap detection"""
    from lionagi_qe.agents.coverage_analyzer import CoverageAnalyzerAgent
    from lionagi_qe.core.task import QETask

    print("\n" + "="*80)
    print("EXAMPLE 2: Coverage Analysis with Streaming")
    print("="*80 + "\n")

    # Create task for coverage analysis
    task = QETask(
        task_type="coverage_analysis",
        context={
            "coverage_data": {
                "files": {
                    "src/utils.py": {"line_coverage": 85, "branch_coverage": 78},
                    "src/models.py": {"line_coverage": 92, "branch_coverage": 88},
                    "src/handlers.py": {"line_coverage": 65, "branch_coverage": 58},
                    "src/validators.py": {"line_coverage": 88, "branch_coverage": 82},
                }
            },
            "framework": "pytest",
            "target_coverage": 85.0,
        }
    )

    print("Task: Analyze coverage for 4 source files")
    print("-" * 80)

    # Track critical issues
    high_severity_gaps = []
    critical_paths = []

    # Stream coverage analysis
    # async for event in agent.analyze_coverage_streaming(task):
    #     if event["type"] == "progress":
    #         print(f"[{event['files_analyzed']}/{event['total_files']}] {event['message']}")
    #
    #     elif event["type"] == "gap":
    #         gap = event["gap"]
    #         severity_emoji = {
    #             "low": "🟢",
    #             "medium": "🟡",
    #             "high": "🔴",
    #             "critical": "🔴🔴"
    #         }.get(gap["severity"], "⚪")
    #
    #         print(f"{severity_emoji} Gap: {gap['file_path']} (lines {gap['line_start']}-{gap['line_end']})")
    #
    #         if gap["severity"] in ["high", "critical"]:
    #             high_severity_gaps.append(gap)
    #             print(f"   ⚠️  Suggested: {', '.join(gap['suggested_tests'])}")
    #
    #     elif event["type"] == "critical_path":
    #         critical_paths.append(event["path"])
    #         print(f"🎯 Critical Path: {event['path']}")
    #
    #     elif event["type"] == "complete":
    #         print("-" * 80)
    #         print(f"📊 Overall Coverage: {event['overall_coverage']}%")
    #         print(f"   Line Coverage: {event['line_coverage']}%")
    #         print(f"   Branch Coverage: {event['branch_coverage']}%")
    #         print(f"🔍 Total Gaps: {event['gaps_count']}")
    #         print(f"🎯 Critical Paths: {event['critical_paths_count']}")
    #         print(f"⏱️  Analysis Time: {event['analysis_time_ms']}ms")
    #
    #         if event['meets_threshold']:
    #             print("✅ Meets coverage threshold")
    #         else:
    #             print(f"❌ Below threshold (target: 85%)")

    print("\nAPI Usage Pattern:")
    print("""
    critical_issues = []

    async for event in agent.analyze_coverage_streaming(task):
        if event["type"] == "gap" and event["gap"]["severity"] == "high":
            # Alert immediately on critical gaps
            send_alert(event["gap"])
            critical_issues.append(event["gap"])

        elif event["type"] == "critical_path":
            # Track critical execution paths
            track_critical_path(event["path"])

        elif event["type"] == "complete":
            # Generate final report
            generate_report(event, critical_issues)
    """)


# Example 3: Using MCP Streaming Tools
async def example_mcp_streaming_usage():
    """Example: Use streaming via MCP tools"""
    print("\n" + "="*80)
    print("EXAMPLE 3: MCP Streaming Tools")
    print("="*80 + "\n")

    print("Usage in Claude Code:")
    print("-" * 80)
    print("""
    # Import MCP streaming tools
    from lionagi_qe.mcp.mcp_tools import (
        test_generate_stream,
        coverage_analyze_stream,
        test_execute_stream
    )

    # Example 1: Stream test generation
    code = '''
    def validate_email(email: str) -> bool:
        return '@' in email and '.' in email.split('@')[1]
    '''

    async for event in test_generate_stream(
        code=code,
        framework="pytest",
        test_type="unit",
        target_count=5
    ):
        if event["type"] == "test":
            print(f"Generated: {event['test_case']['test_name']}")
        elif event["type"] == "complete":
            print(f"Done! {event['total']} tests generated")

    # Example 2: Stream coverage analysis
    async for event in coverage_analyze_stream(
        source_path="./src",
        coverage_data=coverage_json,
        framework="pytest"
    ):
        if event["type"] == "gap":
            print(f"Gap found: {event['gap']['file_path']}")
        elif event["type"] == "complete":
            print(f"Coverage: {event['overall_coverage']}%")

    # Example 3: Stream test execution
    async for event in test_execute_stream(
        test_path="./tests",
        framework="pytest",
        parallel=True
    ):
        if event["type"] == "progress":
            print(f"Running tests: {event['percent']}%")
        elif event["type"] == "result":
            result = event["data"]
            print(f"Passed: {result['passed']}, Failed: {result['failed']}")
    """)


# Example 4: Building a Progress Dashboard
async def example_progress_dashboard():
    """Example: Build a real-time progress dashboard"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Real-Time Progress Dashboard")
    print("="*80 + "\n")

    print("Dashboard Implementation:")
    print("-" * 80)
    print("""
    class QEProgressDashboard:
        def __init__(self):
            self.current_operation = None
            self.progress = 0
            self.events = []
            self.metrics = {
                "tests_generated": 0,
                "gaps_found": 0,
                "critical_paths": 0,
                "coverage": 0.0
            }

        async def track_test_generation(self, agent, task):
            self.current_operation = "Generating Tests"

            async for event in agent.generate_tests_streaming(task):
                self.events.append(event)

                if event["type"] == "progress":
                    self.progress = event["percent"]
                    self.update_display()

                elif event["type"] == "test":
                    self.metrics["tests_generated"] += 1
                    self.update_display()

                elif event["type"] == "complete":
                    self.metrics["coverage"] = event["coverage_estimate"]
                    self.current_operation = "Complete"
                    self.update_display()

        async def track_coverage_analysis(self, agent, task):
            self.current_operation = "Analyzing Coverage"

            async for event in agent.analyze_coverage_streaming(task):
                self.events.append(event)

                if event["type"] == "progress":
                    self.progress = event["percent"]
                    self.update_display()

                elif event["type"] == "gap":
                    self.metrics["gaps_found"] += 1
                    self.update_display()

                elif event["type"] == "critical_path":
                    self.metrics["critical_paths"] += 1
                    self.update_display()

                elif event["type"] == "complete":
                    self.metrics["coverage"] = event["overall_coverage"]
                    self.current_operation = "Complete"
                    self.update_display()

        def update_display(self):
            # Clear screen and show updated dashboard
            print(f"\\033[2J\\033[H")  # Clear screen
            print("=" * 80)
            print(f"QE Fleet Dashboard - {self.current_operation}")
            print("=" * 80)
            print(f"Progress: [{self._progress_bar()}] {self.progress:.1f}%")
            print()
            print(f"Metrics:")
            print(f"  Tests Generated: {self.metrics['tests_generated']}")
            print(f"  Gaps Found: {self.metrics['gaps_found']}")
            print(f"  Critical Paths: {self.metrics['critical_paths']}")
            print(f"  Coverage: {self.metrics['coverage']:.1f}%")
            print("=" * 80)

        def _progress_bar(self):
            filled = int(40 * self.progress / 100)
            return "█" * filled + "░" * (40 - filled)

    # Usage
    dashboard = QEProgressDashboard()
    await dashboard.track_test_generation(agent, task)
    await dashboard.track_coverage_analysis(agent, task)
    """)


# Example 5: Error Handling with Streaming
async def example_error_handling():
    """Example: Handle errors gracefully during streaming"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Error Handling with Streaming")
    print("="*80 + "\n")

    print("Error Handling Pattern:")
    print("-" * 80)
    print("""
    async def safe_streaming_operation(agent, task):
        try:
            partial_results = []

            async for event in agent.generate_tests_streaming(task):
                if event["type"] == "error":
                    # Handle error event
                    print(f"Error: {event['message']}")
                    print(f"Partial results: {len(partial_results)} items")

                    # Optionally retry or fallback
                    return partial_results

                elif event["type"] == "test":
                    # Save partial results as we go
                    partial_results.append(event["test_case"])

                elif event["type"] == "complete":
                    return event["tests"]

        except Exception as e:
            # Handle streaming exceptions
            print(f"Streaming failed: {e}")
            print(f"Saved {len(partial_results)} partial results")
            return partial_results

    # Graceful degradation
    results = await safe_streaming_operation(agent, task)
    if results:
        print(f"Got {len(results)} results (complete or partial)")
    """)


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("STREAMING PROGRESS - USAGE EXAMPLES")
    print("Agentic QE Fleet v1.4.1")
    print("="*80)

    await example_test_generation_streaming()
    await asyncio.sleep(0.5)

    await example_coverage_analysis_streaming()
    await asyncio.sleep(0.5)

    await example_mcp_streaming_usage()
    await asyncio.sleep(0.5)

    await example_progress_dashboard()
    await asyncio.sleep(0.5)

    await example_error_handling()

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETE")
    print("="*80 + "\n")
    print("Key Takeaways:")
    print("  ✓ Streaming provides real-time feedback")
    print("  ✓ Use async for loops to consume streams")
    print("  ✓ Handle different event types appropriately")
    print("  ✓ Implement error handling for robustness")
    print("  ✓ Save partial results for resilience")
    print()


if __name__ == "__main__":
    asyncio.run(main())
