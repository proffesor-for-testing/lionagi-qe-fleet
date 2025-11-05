#!/usr/bin/env python3
"""
Quick verification that all agents support memory backends
"""

import inspect
from pathlib import Path
import importlib.util

def load_agent_class(file_path: Path):
    """Dynamically load agent class from file"""
    spec = importlib.util.spec_from_file_location("agent_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the agent class (inherits from BaseQEAgent)
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) and
            hasattr(obj, '__bases__') and
            any('BaseQEAgent' in str(base) for base in obj.__bases__)):
            return obj
    return None

def verify_agent(file_path: Path) -> dict:
    """Verify an agent has memory backend support"""
    result = {
        "file": file_path.name,
        "has_init": False,
        "has_memory_param": False,
        "has_memory_config_param": False,
        "signature": None
    }

    try:
        agent_class = load_agent_class(file_path)
        if not agent_class:
            result["error"] = "Could not find agent class"
            return result

        # Check __init__ method
        if hasattr(agent_class, '__init__'):
            result["has_init"] = True
            sig = inspect.signature(agent_class.__init__)
            result["signature"] = str(sig)

            # Check parameters
            params = sig.parameters
            result["has_memory_param"] = 'memory' in params
            result["has_memory_config_param"] = 'memory_config' in params

    except Exception as e:
        result["error"] = str(e)

    return result

def main():
    """Main verification"""
    print("="*80)
    print("MEMORY BACKEND INTEGRATION VERIFICATION")
    print("="*80 + "\n")

    agents_dir = Path("src/lionagi_qe/agents")
    agent_files = [f for f in agents_dir.glob("*.py")
                   if f.name != "__init__.py"]

    print(f"Found {len(agent_files)} agent files\n")

    results = []
    for file_path in sorted(agent_files):
        result = verify_agent(file_path)
        results.append(result)

    # Summary
    total = len(results)
    with_init = sum(1 for r in results if r["has_init"])
    with_memory = sum(1 for r in results if r["has_memory_param"])
    with_memory_config = sum(1 for r in results if r["has_memory_config_param"])

    print(f"Results:")
    print(f"  Total agents:                {total}")
    print(f"  With __init__:               {with_init}/{total}")
    print(f"  With memory parameter:       {with_memory}/{total}")
    print(f"  With memory_config parameter: {with_memory_config}/{total}")

    # Details
    print("\n" + "-"*80)
    print("Details:")
    print("-"*80)

    for result in results:
        status = "✓" if (result["has_memory_param"] and
                        result["has_memory_config_param"]) else "✗"
        print(f"{status} {result['file']:30s} ", end="")

        if result.get("error"):
            print(f"ERROR: {result['error']}")
        elif not result["has_init"]:
            print("No __init__ method")
        elif not result["has_memory_param"]:
            print("Missing 'memory' parameter")
        elif not result["has_memory_config_param"]:
            print("Missing 'memory_config' parameter")
        else:
            print("OK - Memory backend supported")

    # Final verdict
    print("\n" + "="*80)
    if with_memory == total and with_memory_config == total:
        print("✓ SUCCESS: All agents support memory backends!")
    else:
        print(f"⚠ WARNING: {total - with_memory} agents still need updates")
    print("="*80)

if __name__ == "__main__":
    main()
