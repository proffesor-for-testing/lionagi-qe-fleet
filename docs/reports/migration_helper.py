#!/usr/bin/env python3
"""
Migration Helper for PostgresMemory/RedisMemory Integration

This script helps migrate existing code to use the new persistent memory backends.
It provides examples, validation, and automated migration suggestions.

Usage:
    python migration_helper.py --scan ./your_code_dir
    python migration_helper.py --examples
    python migration_helper.py --validate ./your_code_dir
"""

import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple

# ANSI colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{text}{Colors.END}")
    print(f"{'-'*len(text)}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def show_examples():
    """Show migration examples"""
    print_header("MIGRATION EXAMPLES")

    # Example 1: Simple agent creation
    print_section("Example 1: Migrating Simple Agent Creation")
    print(f"{Colors.BOLD}BEFORE (using QEMemory):{Colors.END}")
    print("""
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.agents import TestGeneratorAgent

memory = QEMemory()
agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model
)
""")

    print(f"\n{Colors.BOLD}AFTER (using PostgresMemory):{Colors.END}")
    print("""
from lionagi_qe.learning import DatabaseManager
from lionagi_qe.persistence import PostgresMemory
from lionagi_qe.agents import TestGeneratorAgent

# Option 1: Pass memory directly
db_manager = DatabaseManager("postgresql://user:pass@localhost:5432/lionagi_qe_learning")
await db_manager.connect()
memory = PostgresMemory(db_manager)

agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model,
    memory=memory  # Persistent memory!
)

# Option 2: Use memory_config (auto-initialization)
agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model,
    memory_config={"type": "postgres", "db_manager": db_manager}
)

# Option 3: Default (Session.context - in-memory)
agent = TestGeneratorAgent(
    agent_id="test-generator",
    model=model
    # No memory parameter = Session.context (backward compatible)
)
""")

    # Example 2: Redis backend
    print_section("Example 2: Using RedisMemory (High-Speed Cache)")
    print("""
from lionagi_qe.persistence import RedisMemory
from lionagi_qe.agents import CoverageAnalyzerAgent

# Create Redis memory backend
memory = RedisMemory(
    host="localhost",
    port=6379,
    db=0,
    max_connections=10
)

agent = CoverageAnalyzerAgent(
    agent_id="coverage-analyzer",
    model=model,
    memory=memory
)

# Cleanup when done
memory.close()
""")

    # Example 3: Orchestrator with memory backends
    print_section("Example 3: Using QEOrchestrator with Memory Backends")
    print("""
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.agents import TestGeneratorAgent, CoverageAnalyzerAgent

# Option 1: Auto-detect from environment
orchestrator = QEOrchestrator.from_environment()
await orchestrator.connect()

# Create agents - they automatically share the orchestrator's memory backend
test_gen = orchestrator.create_and_register_agent(
    TestGeneratorAgent,
    agent_id="test-generator",
    model=model
)

coverage = orchestrator.create_and_register_agent(
    CoverageAnalyzerAgent,
    agent_id="coverage-analyzer",
    model=model
)

# Agents now share the same memory backend!
# They can coordinate through shared memory keys like "aqe/coverage/gaps"

# Option 2: Explicit mode
orchestrator = QEOrchestrator(
    mode="prod",
    database_url="postgresql://user:pass@localhost:5432/lionagi_qe_learning"
)
await orchestrator.connect()

# Create agents with shared memory
memory_config = orchestrator.get_memory_config_for_agents()
agent = TestGeneratorAgent(
    agent_id="test-gen",
    model=model,
    memory_config=memory_config
)
orchestrator.register_agent(agent)
""")

    # Example 4: Environment-based configuration
    print_section("Example 4: Environment-Based Configuration")
    print("""
# Set environment variables
export AQE_STORAGE_MODE=production
export DATABASE_URL=postgresql://user:pass@localhost:5432/lionagi_qe_learning
export AQE_POOL_MIN=2
export AQE_POOL_MAX=10

# Then in your code:
from lionagi_qe.core.orchestrator import QEOrchestrator

# Auto-detects production mode and uses PostgresMemory
orchestrator = QEOrchestrator.from_environment()
await orchestrator.connect()

# All agents created through orchestrator use PostgresMemory
agent = orchestrator.create_and_register_agent(
    TestGeneratorAgent,
    agent_id="test-gen",
    model=model
)
""")

def scan_code(directory: Path) -> List[Tuple[Path, int, str]]:
    """Scan code for patterns that need migration"""
    patterns = [
        (r'QEMemory\(\)', "QEMemory() - Consider migrating to PostgresMemory or RedisMemory"),
        (r'from lionagi_qe\.core\.memory import QEMemory',
         "QEMemory import - Consider using PostgresMemory or RedisMemory"),
        (r'agent_id=["\'][^"\']+["\'],\s*model=\w+\)',
         "Agent initialization without memory parameter - Consider adding memory backend"),
    ]

    findings = []

    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path) or "migration_helper.py" in str(file_path):
            continue

        try:
            content = file_path.read_text()
            for pattern, description in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Count line number
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append((file_path, line_num, description))
        except Exception as e:
            print_warning(f"Could not scan {file_path}: {e}")

    return findings

def validate_migration(directory: Path) -> Dict[str, List]:
    """Validate that migration is complete"""
    results = {
        "agents_with_init": [],
        "agents_without_init": [],
        "orchestrator_updated": False,
        "uses_postgres_memory": False,
        "uses_redis_memory": False,
    }

    # Check agents
    agents_dir = directory / "src" / "lionagi_qe" / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name == "__init__.py":
                continue

            content = agent_file.read_text()
            if "def __init__" in content and "memory_config" in content:
                results["agents_with_init"].append(agent_file.name)
            elif "class" in content and "BaseQEAgent" in content:
                results["agents_without_init"].append(agent_file.name)

    # Check orchestrator
    orchestrator_file = directory / "src" / "lionagi_qe" / "core" / "orchestrator.py"
    if orchestrator_file.exists():
        content = orchestrator_file.read_text()
        results["orchestrator_updated"] = (
            "create_and_register_agent" in content and
            "get_memory_config_for_agents" in content
        )

    # Check if persistence modules are imported
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue

        try:
            content = file_path.read_text()
            if "PostgresMemory" in content:
                results["uses_postgres_memory"] = True
            if "RedisMemory" in content:
                results["uses_redis_memory"] = True
        except:
            pass

    return results

def print_validation_results(results: Dict):
    """Print validation results"""
    print_header("MIGRATION VALIDATION RESULTS")

    # Agent status
    print_section("Agent Migration Status")
    total_agents = len(results["agents_with_init"]) + len(results["agents_without_init"])
    migrated_agents = len(results["agents_with_init"])

    if migrated_agents == total_agents and total_agents > 0:
        print_success(f"All {total_agents} agents have memory backend support!")
    elif migrated_agents > 0:
        print_warning(f"{migrated_agents}/{total_agents} agents migrated")
        if results["agents_without_init"]:
            print("\nAgents still needing migration:")
            for agent in results["agents_without_init"]:
                print(f"  - {agent}")
    else:
        print_error("No agents have been migrated yet")

    # Orchestrator status
    print_section("Orchestrator Status")
    if results["orchestrator_updated"]:
        print_success("Orchestrator has memory backend support methods")
    else:
        print_warning("Orchestrator may need updates for memory backend support")

    # Memory backend usage
    print_section("Memory Backend Usage")
    if results["uses_postgres_memory"]:
        print_success("PostgresMemory is being used")
    else:
        print_warning("PostgresMemory not detected (may still be using QEMemory)")

    if results["uses_redis_memory"]:
        print_success("RedisMemory is being used")
    else:
        print("  RedisMemory not detected (optional)")

def main():
    """Main migration helper"""
    parser = argparse.ArgumentParser(
        description="Migration helper for PostgresMemory/RedisMemory integration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show migration examples"
    )

    parser.add_argument(
        "--scan",
        type=Path,
        metavar="DIR",
        help="Scan directory for code that needs migration"
    )

    parser.add_argument(
        "--validate",
        type=Path,
        metavar="DIR",
        help="Validate that migration is complete"
    )

    args = parser.parse_args()

    if args.examples:
        show_examples()

    elif args.scan:
        if not args.scan.exists():
            print_error(f"Directory not found: {args.scan}")
            return

        print_header("SCANNING FOR MIGRATION OPPORTUNITIES")
        print(f"Scanning directory: {args.scan}\n")

        findings = scan_code(args.scan)

        if not findings:
            print_success("No migration opportunities found!")
        else:
            print(f"Found {len(findings)} potential migration opportunities:\n")
            for file_path, line_num, description in findings:
                print(f"{Colors.YELLOW}{file_path}:{line_num}{Colors.END}")
                print(f"  {description}\n")

    elif args.validate:
        if not args.validate.exists():
            print_error(f"Directory not found: {args.validate}")
            return

        results = validate_migration(args.validate)
        print_validation_results(results)

    else:
        parser.print_help()
        print("\n" + "="*80)
        print("Quick start:")
        print("  python migration_helper.py --examples        # View migration examples")
        print("  python migration_helper.py --scan .          # Scan for migration opportunities")
        print("  python migration_helper.py --validate .      # Validate migration completion")
        print("="*80)

if __name__ == "__main__":
    main()
