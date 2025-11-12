"""
Example usage of AQE Fleet API Python SDK.

This example demonstrates all major API operations including:
- Test generation
- Test execution
- Coverage analysis
- Quality gate validation
- Security scanning
- Performance testing
- Job monitoring with WebSocket streaming
"""

import asyncio
from lionagi_qe.api.sdk import AQEClient


async def main():
    """Demonstrate AQE Fleet API usage."""

    # Initialize client
    async with AQEClient(
        api_key="aqe_your_api_key_here", base_url="http://localhost:8080"
    ) as client:

        print("=== AQE Fleet API Example ===\n")

        # 1. Check Fleet Status
        print("1. Checking fleet status...")
        fleet_status = await client.get_fleet_status(verbose=True, include_metrics=True)
        print(f"   Active agents: {fleet_status['active_agents']}")
        print(f"   Queued jobs: {fleet_status['queued_jobs']}")
        print()

        # 2. Generate Tests
        print("2. Generating unit tests...")
        job = await client.generate_tests(
            target="src/services/user.service.ts",
            framework="jest",
            test_type="unit",
            coverage_target=90.0,
            priority="high",
        )
        job_id = job["job_id"]
        print(f"   Job created: {job_id}")
        print(f"   Status: {job['status']}")
        print()

        # 3. Stream Job Progress (WebSocket)
        print("3. Streaming job progress...")
        async for update in client.stream_job_progress(job_id):
            if update["type"] == "progress":
                print(
                    f"   {update['progress']:.1f}%: {update.get('message', 'Processing...')}"
                )
            elif update["type"] == "complete":
                print("   Job completed!")
                print(f"   Result: {update.get('result')}")
                break
            elif update["type"] == "error":
                print(f"   Error: {update.get('error')}")
                break
        print()

        # 4. Execute Tests
        print("4. Executing tests...")
        exec_job = await client.execute_tests(
            test_path="tests/",
            framework="jest",
            parallel=True,
            coverage=True,
            timeout=300,
        )
        print(f"   Job created: {exec_job['job_id']}")
        print()

        # 5. Analyze Coverage
        print("5. Analyzing coverage...")
        cov_job = await client.analyze_coverage(
            source_path="src/",
            test_path="tests/",
            min_coverage=80.0,
            include_gaps=True,
        )
        print(f"   Job created: {cov_job['job_id']}")
        print()

        # 6. Validate Quality Gate
        print("6. Validating quality gates...")
        quality_job = await client.validate_quality_gate(
            project_path=".",
            min_coverage=80.0,
            max_complexity=10,
            max_duplicates=3.0,
            security_checks=True,
            priority="high",
        )
        print(f"   Job created: {quality_job['job_id']}")
        print()

        # 7. Security Scan
        print("7. Running security scan...")
        security_job = await client.scan_security(
            target=".",
            scan_dependencies=True,
            scan_code=True,
            severity_threshold="medium",
            priority="high",
        )
        print(f"   Job created: {security_job['job_id']}")
        print()

        # 8. Performance Test
        print("8. Running performance test...")
        perf_job = await client.run_performance_test(
            target_url="https://api.example.com/users",
            duration_seconds=30,
            virtual_users=10,
            ramp_up_seconds=5,
            think_time_ms=1000,
        )
        print(f"   Job created: {perf_job['job_id']}")
        print()

        # 9. Wait for All Jobs to Complete
        print("9. Waiting for jobs to complete...")
        job_ids = [
            exec_job["job_id"],
            cov_job["job_id"],
            quality_job["job_id"],
            security_job["job_id"],
            perf_job["job_id"],
        ]

        for job_id in job_ids:
            while True:
                status = await client.get_job_status(job_id)
                if status["status"] in ["completed", "failed"]:
                    print(f"   {job_id}: {status['status']}")
                    break
                await asyncio.sleep(2)
        print()

        # 10. Get Job Results
        print("10. Fetching job results...")
        for job_id in job_ids[:2]:  # Show results for first 2 jobs
            result = await client.get_job_result(job_id)
            print(f"   {job_id}:")
            print(f"     Status: {result['status']}")
            if result.get("result"):
                print(f"     Result: {result['result']}")
        print()

        print("=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
