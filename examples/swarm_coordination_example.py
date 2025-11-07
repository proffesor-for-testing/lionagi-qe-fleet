"""
Example: Continuous Risk/Dependency Tracking with Swarm Coordination

Demonstrates integration of:
- RiskDependencyTracker (ROAM + dependency graph)
- WIPLimitedOrchestrator (agent lane segregation)
- Async background monitoring
- Traffic light prioritization (🟢🟡🔴)

Usage:
    python examples/swarm_coordination_example.py
"""

import asyncio
import json
from datetime import datetime

# Assuming these imports work in the actual environment
try:
    from lionagi_qe.tracking.risk_dependency_tracker import (
        RiskDependencyTracker,
        RiskStatus,
        DependencyStatus,
        TrafficLight,
        create_tracker_for_sprint
    )
    from lionagi_qe.core.orchestrator_wip import (
        WIPLimitedOrchestrator,
        LaneType,
        create_wip_limited_orchestrator
    )
except ImportError:
    print("Note: This example requires lionagi-qe-fleet to be installed")
    print("Run: pip install -e .")
    exit(1)


async def example_qe_sprint_with_tracking():
    """
    Example: QE Sprint with continuous risk/dependency tracking
    
    Scenario:
    - Sprint goal: Implement WIP limits for orchestrator
    - Multiple dependencies and risks
    - Continuous monitoring for blockers
    - Swarm coordination via traffic lights
    """
    
    print("=" * 70)
    print("QE SPRINT: WIP Limits Implementation with Risk Tracking")
    print("=" * 70)
    print()
    
    # 1. Create tracker for 2-week sprint
    tracker = create_tracker_for_sprint(sprint_duration_days=14)
    
    # 2. Define risks (ROAM methodology)
    print("📋 ADDING RISKS TO TRACKER")
    print("-" * 70)
    
    risk1 = tracker.add_risk(
        risk_id="RISK-001",
        description="Backtesting framework missing - APRA system unvalidated",
        probability=0.9,
        impact=0.95,
        owner="validation_team",
        tags={"trading", "validation", "critical"}
    )
    print(f"  {risk1.traffic_light.value} RISK-001: {risk1.description}")
    print(f"     Score: {risk1.risk_score:.2f} | Status: {risk1.status.value}")
    
    risk2 = tracker.add_risk(
        risk_id="RISK-002",
        description="WIP limit enforcement may cause performance degradation",
        probability=0.4,
        impact=0.6,
        owner="qe_team",
        tags={"performance", "orchestrator"}
    )
    print(f"  {risk2.traffic_light.value} RISK-002: {risk2.description}")
    print(f"     Score: {risk2.risk_score:.2f} | Status: {risk2.status.value}")
    
    risk3 = tracker.add_risk(
        risk_id="RISK-003",
        description="Context budget tracking has no validation",
        probability=0.3,
        impact=0.4,
        owner="qe_team",
        tags={"testing", "validation"}
    )
    print(f"  {risk3.traffic_light.value} RISK-003: {risk3.description}")
    print(f"     Score: {risk3.risk_score:.2f} | Status: {risk3.status.value}")
    print()
    
    # 3. Define dependencies
    print("📋 ADDING DEPENDENCIES TO TRACKER")
    print("-" * 70)
    
    # Phase 1 tasks (from Quick Wins doc)
    dep1 = tracker.add_dependency(
        task_id="TASK-001",
        description="Create RCA document (5W analysis)",
        lane="documentation",
        assignee="analyst",
        tags={"phase1", "documentation"}
    )
    print(f"  {dep1.traffic_light.value} TASK-001: {dep1.description}")
    print(f"     Status: {dep1.status.value} | Lane: {dep1.lane}")
    
    dep2 = tracker.add_dependency(
        task_id="TASK-002",
        description="Implement WIP-limited orchestrator",
        depends_on={"TASK-001"},  # Needs RCA first
        lane="implementation",
        assignee="engineer",
        tags={"phase1", "implementation"}
    )
    print(f"  {dep2.traffic_light.value} TASK-002: {dep2.description}")
    print(f"     Status: {dep2.status.value} | Depends on: {dep2.depends_on}")
    
    dep3 = tracker.add_dependency(
        task_id="TASK-003",
        description="Create unit test suite (19 tests)",
        depends_on={"TASK-002"},
        blocked_by={"RISK-003"},  # Need context budget validation
        lane="testing",
        assignee="test_engineer",
        tags={"phase1", "testing"}
    )
    print(f"  {dep3.traffic_light.value} TASK-003: {dep3.description}")
    print(f"     Status: {dep3.status.value} | Blocked by: {dep3.blocked_by}")
    
    # Phase 2 tasks
    dep4 = tracker.add_dependency(
        task_id="TASK-004",
        description="Run integration tests with real agents",
        depends_on={"TASK-003"},
        lane="testing",
        assignee="test_engineer",
        tags={"phase2", "integration"}
    )
    print(f"  {dep4.traffic_light.value} TASK-004: {dep4.description}")
    
    dep5 = tracker.add_dependency(
        task_id="TASK-005",
        description="Benchmark WIP-limited vs baseline",
        depends_on={"TASK-004"},
        lane="performance",
        assignee="perf_engineer",
        tags={"phase2", "benchmarking"}
    )
    print(f"  {dep5.traffic_light.value} TASK-005: {dep5.description}")
    
    # APRA trading tasks (BLOCKED by RISK-001)
    dep6 = tracker.add_dependency(
        task_id="TASK-006",
        description="APRA: Implement backtesting framework",
        blocked_by={"RISK-001"},
        lane="trading",
        assignee="trading_team",
        tags={"apra", "validation", "blocked"}
    )
    print(f"  {dep6.traffic_light.value} TASK-006: {dep6.description}")
    print(f"     Status: {dep6.status.value} | Blocked by: {dep6.blocked_by}")
    print()
    
    # 4. Start continuous monitoring
    print("🔄 STARTING CONTINUOUS MONITORING")
    print("-" * 70)
    print("  Monitoring interval: 30s (sprint mode)")
    print("  Risk threshold: 0.6")
    print("  Swarm alerts: ENABLED")
    print()
    
    await tracker.start_monitoring()
    
    # 5. Simulate sprint progress
    print("⏳ SIMULATING SPRINT PROGRESS...")
    print("-" * 70)
    print()
    
    await asyncio.sleep(1)  # Simulate time passing
    
    # Complete TASK-001 (RCA)
    print("✅ TASK-001 COMPLETED: RCA document")
    tracker.update_dependency_status("TASK-001", DependencyStatus.COMPLETE)
    dep2_status = tracker.dependencies["TASK-002"]
    print(f"   → TASK-002 status: {dep2_status.status.value} (unblocked)")
    print()
    
    await asyncio.sleep(1)
    
    # Mitigate RISK-003 (context budget validation)
    print("✅ RISK-003 MITIGATED: Context budget validation added")
    tracker.update_risk_status(
        "RISK-003",
        RiskStatus.MITIGATED,
        mitigation_plan="Added validation in test suite"
    )
    dep3_status = tracker.dependencies["TASK-003"]
    print(f"   → TASK-003 status: {dep3_status.status.value}")
    print()
    
    await asyncio.sleep(1)
    
    # Complete TASK-002 (orchestrator)
    print("✅ TASK-002 COMPLETED: WIP-limited orchestrator (474 lines)")
    tracker.update_dependency_status("TASK-002", DependencyStatus.COMPLETE)
    dep3_status = tracker.dependencies["TASK-003"]
    print(f"   → TASK-003 status: {dep3_status.status.value} (ready!)")
    print()
    
    # 6. Get status report
    print("📊 CURRENT STATUS REPORT")
    print("=" * 70)
    
    status = tracker.get_status_report()
    print(json.dumps(status, indent=2, default=str))
    print()
    
    # 7. Get swarm recommendations
    print("💡 SWARM COORDINATION RECOMMENDATIONS")
    print("=" * 70)
    
    for rec in status["recommendations"]:
        print(f"  {rec}")
    print()
    
    # 8. Check alerts
    print("🚨 UNACKNOWLEDGED ALERTS")
    print("=" * 70)
    
    alerts = tracker.get_unacknowledged_alerts()
    for alert in alerts[:5]:  # Show top 5
        print(f"  {alert.severity.value} [{alert.alert_type}] {alert.message}")
        print(f"     ID: {alert.alert_id} | Time: {alert.created_at.strftime('%H:%M:%S')}")
    print(f"\n  Total unacknowledged: {len(alerts)}")
    print()
    
    # 9. Detect bottlenecks
    print("🔍 BOTTLENECK ANALYSIS")
    print("=" * 70)
    
    bottlenecks = tracker.detect_bottlenecks()
    if bottlenecks:
        for task_id, count in bottlenecks[:3]:
            print(f"  ⚠️  {task_id}: {count} tasks depend on this")
    else:
        print("  ✅ No bottlenecks detected")
    print()
    
    # 10. Critical path analysis
    print("🛤️  CRITICAL PATH ANALYSIS")
    print("=" * 70)
    
    critical_path = tracker.get_critical_path()
    print(f"  Critical path length: {len(critical_path)} tasks")
    print(f"  Tasks: {' → '.join(critical_path)}")
    print()
    
    # 11. Lane status (for swarm coordination)
    print("🏊 SWARM LANE STATUS")
    print("=" * 70)
    
    lanes = ["documentation", "implementation", "testing", "performance", "trading"]
    for lane in lanes:
        ready_tasks = tracker.get_ready_tasks_by_lane(lane)
        if ready_tasks:
            status_emoji = TrafficLight.GREEN.value
        else:
            blocked = [d for d in tracker.get_blocked_tasks() if d.lane == lane]
            status_emoji = TrafficLight.RED.value if blocked else TrafficLight.YELLOW.value
        
        print(f"  {status_emoji} {lane.upper():15} - {len(ready_tasks)} ready task(s)")
    print()
    
    # 12. Stop monitoring
    print("🛑 STOPPING MONITORING")
    print("-" * 70)
    
    await tracker.stop_monitoring()
    
    print(f"  Total monitoring cycles: {tracker.metrics['monitoring_cycles']}")
    print(f"  Total alerts generated: {tracker.metrics['alerts_generated']}")
    print(f"  Risks resolved: {tracker.metrics['risks_resolved']}/{tracker.metrics['risks_created']}")
    print(f"  Dependencies completed: {tracker.metrics['dependencies_completed']}/{len(tracker.dependencies)}")
    print()
    
    # 13. Final summary
    print("=" * 70)
    print("SPRINT SUMMARY")
    print("=" * 70)
    print()
    print("✅ COMPLETED:")
    print("  - RCA document (TASK-001)")
    print("  - WIP-limited orchestrator (TASK-002)")
    print("  - Risk RISK-003 mitigated")
    print()
    print("🔴 BLOCKED:")
    print("  - APRA trading system (TASK-006) - awaiting backtesting framework")
    print(f"    Risk RISK-001: {risk1.risk_score:.2f} score (HIGH PRIORITY)")
    print()
    print("🟢 READY:")
    print("  - Unit test suite (TASK-003) - can proceed")
    print()
    print("📊 METRICS:")
    print(f"  - Risk resolution rate: {status['risks']['resolution_rate']:.0%}")
    print(f"  - Dependency completion rate: {status['dependencies']['completion_rate']:.0%}")
    print(f"  - Bottlenecks detected: {status['bottlenecks']['count']}")
    print(f"  - Critical path length: {status['critical_path']['length']}")
    print()


async def example_with_wip_orchestrator_integration():
    """
    Example: Integrate tracker with WIP-limited orchestrator
    
    Shows how to use tracker to coordinate agent lanes based on
    dependency status and risk levels.
    """
    
    print("=" * 70)
    print("INTEGRATION: Tracker + WIP-Limited Orchestrator")
    print("=" * 70)
    print()
    
    # Create both tracker and orchestrator
    tracker = create_tracker_for_sprint()
    orchestrator = create_wip_limited_orchestrator(wip_limit=5)
    
    print("🔧 SETUP:")
    print(f"  - Tracker monitoring interval: {tracker.monitoring_interval}s")
    print(f"  - Orchestrator WIP limit: {orchestrator.wip_limit}")
    print(f"  - Agent lanes: {list(orchestrator.lanes.keys())}")
    print()
    
    # Add dependencies matching agent lanes
    tracker.add_dependency(
        task_id="test-generation",
        description="Generate test cases",
        lane="test",  # Matches LaneType.TEST
        assignee="test-generator-agent"
    )
    
    tracker.add_dependency(
        task_id="security-scan",
        description="Run security scanner",
        lane="security",  # Matches LaneType.SECURITY
        assignee="security-scanner-agent"
    )
    
    tracker.add_dependency(
        task_id="performance-test",
        description="Execute performance tests",
        depends_on={"test-generation"},  # Blocked until tests generated
        lane="performance",  # Matches LaneType.PERFORMANCE
        assignee="performance-tester-agent"
    )
    
    print("📋 TASK ROUTING:")
    print("-" * 70)
    
    # Check which lanes have ready work
    for lane_type in orchestrator.lanes.keys():
        lane_name = lane_type.value
        ready_tasks = tracker.get_ready_tasks_by_lane(lane_name)
        
        if ready_tasks:
            print(f"  🟢 {lane_name.upper():12} - {len(ready_tasks)} task(s) ready")
            print(f"      WIP limit: {orchestrator.lanes[lane_type].wip_limit}")
            for task in ready_tasks:
                print(f"      - {task.task_id}: {task.description}")
        else:
            print(f"  🟡 {lane_name.upper():12} - No ready tasks")
    
    print()
    print("💡 COORDINATION INSIGHT:")
    print("  When tracker shows tasks ready in a lane, orchestrator assigns")
    print("  agents from that lane up to the lane's WIP limit.")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" SWARM COORDINATION EXAMPLE")
    print(" Risk/Dependency Tracking + WIP-Limited Orchestrator")
    print("=" * 70 + "\n")
    
    try:
        # Run main example
        asyncio.run(example_qe_sprint_with_tracking())
        
        print("\n" * 2)
        
        # Run integration example
        asyncio.run(example_with_wip_orchestrator_integration())
        
        print("\n" + "=" * 70)
        print(" Example completed successfully!")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\nError running example: {e}")
        import traceback
        traceback.print_exc()
