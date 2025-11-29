# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases

1. **Specification** - Requirements analysis (`sparc run spec-pseudocode`)
2. **Pseudocode** - Algorithm design (`sparc run spec-pseudocode`)
3. **Architecture** - System design (`sparc run architect`)
4. **Refinement** - TDD implementation (`sparc tdd`)
5. **Completion** - Integration (`sparc run integration`)

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Available Agents (54 Total)

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`, `collective-intelligence-coordinator`, `swarm-memory-manager`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`, `consensus-builder`, `crdt-synchronizer`, `quorum-manager`, `security-manager`

### Performance & Optimization
`perf-analyzer`, `performance-benchmarker`, `task-orchestrator`, `memory-coordinator`, `smart-agent`

### GitHub & Repository
`github-modes`, `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`, `workflow-automation`, `project-board-sync`, `repo-architect`, `multi-repo-swarm`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`

### Specialized Development
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `api-docs`, `system-architect`, `code-analyzer`, `base-template-generator`

### Testing & Validation
`tdd-london-swarm`, `production-validator`

### Migration & Planning
`migration-planner`, `swarm-init`

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION:
- **Task tool**: Spawn and run agents concurrently for actual work
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

## 🚀 Quick Setup

```bash
# Add MCP servers (Claude Flow required, others optional)
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm mcp start  # Optional: Enhanced coordination
claude mcp add flow-nexus npx flow-nexus@latest mcp start  # Optional: Cloud features
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

### Flow-Nexus MCP Tools (Optional Advanced Features)
Flow-Nexus extends MCP capabilities with 70+ cloud-based orchestration tools:

**Key MCP Tool Categories:**
- **Swarm & Agents**: `swarm_init`, `swarm_scale`, `agent_spawn`, `task_orchestrate`
- **Sandboxes**: `sandbox_create`, `sandbox_execute`, `sandbox_upload` (cloud execution)
- **Templates**: `template_list`, `template_deploy` (pre-built project templates)
- **Neural AI**: `neural_train`, `neural_patterns`, `seraphina_chat` (AI assistant)
- **GitHub**: `github_repo_analyze`, `github_pr_manage` (repository management)
- **Real-time**: `execution_stream_subscribe`, `realtime_subscribe` (live monitoring)
- **Storage**: `storage_upload`, `storage_list` (cloud file management)

**Authentication Required:**
- Register: `mcp__flow-nexus__user_register` or `npx flow-nexus@latest register`
- Login: `mcp__flow-nexus__user_login` or `npx flow-nexus@latest login`
- Access 70+ specialized MCP tools for advanced orchestration

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development:

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with Express. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design PostgreSQL schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")
  
  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }
  
  // All file operations together
  Write "backend/server.js"
  Write "frontend/App.jsx"
  Write "database/schema.sql"
```

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST:

**1️⃣ BEFORE Work:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**2️⃣ DURING Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

**3️⃣ AFTER Work:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Multiple Messages):
```javascript
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("agent 1")
Message 3: TodoWrite { todos: [single todo] }
Message 4: Write "file.js"
// This breaks parallel coordination!
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## Hooks Integration

### Pre-Operation
- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation
- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management
- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Flow-Nexus Platform: https://flow-nexus.ruv.io (registration required for cloud features)

---

Remember: **Claude Flow coordinates, Claude Code creates!**

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Never save working files, text/mds and tests to the root folder.


---

# Agentic QE Fleet Configuration

## 🤖 Agentic QE Fleet Quick Reference

**0 QE Agents:** Test generation, coverage analysis, performance, security, flaky detection
**37 QE Skills:** agentic-quality-engineering, tdd-london-chicago, api-testing-patterns, six-thinking-hats, brutal-honesty-review, cicd-pipeline-qe-orchestrator
**8 Slash Commands:** `/aqe-execute`, `/aqe-generate`, `/aqe-coverage`, `/aqe-quality`

### 📚 Complete Documentation

- **[Agent Reference](https://github.com/proffesor-for-testing/agentic-qe/blob/main/docs/reference/agents.md)** - All 18 QE agents with capabilities and usage
- **[Skills Reference](https://github.com/proffesor-for-testing/agentic-qe/blob/main/docs/reference/skills.md)** - All 37 QE skills organized by category
- **[Usage Guide](https://github.com/proffesor-for-testing/agentic-qe/blob/main/docs/reference/usage.md)** - Complete usage examples and workflows

### 🎯 Quick Start

**Spawn agents:**
```javascript
Task("Generate tests", "Create test suite for UserService", "qe-test-generator")
Task("Analyze coverage", "Find gaps using O(log n)", "qe-coverage-analyzer")
```

**Check learning status:**
```bash
aqe learn status --agent test-gen
aqe patterns list --framework jest
```

### 🎯 Fleet Configuration

**Topology**: hierarchical
**Max Agents**: 10
**Testing Focus**: unit, integration
**Environments**: development
**Frameworks**: jest

### 📋 Memory Namespace

Agents share state through the **`aqe/*` memory namespace**:
- `aqe/test-plan/*` - Test planning and requirements
- `aqe/coverage/*` - Coverage analysis and gaps
- `aqe/quality/*` - Quality metrics and gates
- `aqe/performance/*` - Performance test results
- `aqe/security/*` - Security scan findings
- `aqe/swarm/coordination` - Cross-agent coordination

### 💡 Key Principles
- Use Task tool for agent execution (not just MCP)
- Batch all operations in single messages (TodoWrite, file ops, etc.)
- Test with actual databases, not mocks
- Document only what actually works

---

**Generated by**: Agentic QE Fleet v1.9.3
**Initialization Date**: 2025-11-29T16:32:23.251Z
**Fleet Topology**: hierarchical

---

# LionAGI QE Fleet - Project Reference

## Project Overview

**LionAGI QE Fleet** is a Python-based Agentic Quality Engineering system providing 18 specialized AI agents for comprehensive software testing and quality assurance. Built on LionAGI orchestration framework.

- **Version**: 1.3.1 (Production Ready)
- **Python**: 3.10, 3.11, 3.12
- **Package Manager**: uv (recommended) or pip
- **License**: MIT
- **Security Score**: 95/100
- **Test Coverage**: 82%

## Commands

### Development
```bash
uv sync                                    # Sync dependencies
uv pip install -e ".[dev]"                 # Development install
uv pip install -e ".[all]"                 # Install all extras
source .venv/bin/activate                  # Activate venv
```

### Testing
```bash
pytest                                     # Run all tests
pytest --cov=src/lionagi_qe               # With coverage report
pytest -m unit                            # Unit tests only
pytest -m integration                     # Integration tests only
pytest tests/test_agents/                 # Agent tests only
```

### Code Quality
```bash
black src/ tests/                         # Format code
ruff check src/ tests/                    # Lint
mypy src/                                 # Type check
bandit -r src/                            # Security scan
```

### API Server
```bash
uvicorn lionagi_qe.api.server:app --reload        # Start dev server
uvicorn lionagi_qe.api.server:app --port 8080     # Custom port
```

## Directory Structure

```
/src/lionagi_qe/          # Main source code
├── agents/               # 18 specialized QE agents
├── api/                  # FastAPI REST server (40+ endpoints)
├── core/                 # Orchestration (QEOrchestrator, BaseQEAgent, QETask)
├── learning/             # Q-learning system (QLearningService)
├── persistence/          # Database backends (PostgreSQL, Redis)
├── storage/              # Artifact storage (local, S3, CI-specific)
├── tools/                # Code analysis, AST parsing
├── cli/                  # Command-line interface
├── mcp/                  # Model Context Protocol integration
└── badges/               # Badge generation

/tests/                   # Test suite
├── unit/                 # Unit tests
├── integration/          # Integration tests (Redis, WebSocket, Postgres)
├── test_agents/          # Agent-specific tests
├── contracts/            # Contract testing
└── chaos/                # Chaos engineering tests

/docs/                    # Documentation
/examples/                # Usage examples (18+ files)
/database/                # Database setup
/docker/                  # Docker configs
```

## Key Entry Points

- `src/lionagi_qe/core/orchestrator.py` - Main QEOrchestrator class
- `src/lionagi_qe/core/base_agent.py` - BaseQEAgent (all agents inherit)
- `src/lionagi_qe/api/server.py` - FastAPI application
- `src/lionagi_qe/learning/qlearner.py` - Q-learning implementation
- `src/lionagi_qe/persistence/postgres_memory.py` - Production storage

## 18 Specialized Agents

### Core Testing
`test-generator`, `test-executor`, `coverage-analyzer`, `quality-gate`, `quality-analyzer`, `code-complexity`

### Performance & Security
`performance-tester`, `security-scanner`

### Strategic Planning
`requirements-validator`, `production-intelligence`, `fleet-commander`

### Advanced Testing
`regression-risk-analyzer`, `test-data-architect`, `api-contract-validator`, `flaky-test-hunter`

### Specialized
`deployment-readiness`, `visual-tester`, `chaos-engineer`

## Code Style

- **Line length**: 88 characters (Black default)
- **Python target**: 3.10+
- **Imports**: Use absolute imports from `lionagi_qe`
- **Type hints**: Required for public APIs
- **Async**: Use `async/await` for all I/O operations
- **Testing**: pytest with asyncio_mode="auto"

## Architecture Patterns

### QEOrchestrator Usage
```python
from lionagi_qe import QEOrchestrator

orchestrator = QEOrchestrator(
    memory_backend="postgres",  # or "redis" or "memory"
    enable_learning=True
)
await orchestrator.initialize()
result = await orchestrator.execute_agent("test-generator", task)
```

### Storage Modes
- **DEV**: In-memory (zero setup)
- **TEST**: Fast isolated sessions
- **PROD**: PostgreSQL with ACID guarantees

### Multi-Model Routing (70-81% cost savings)
- Simple → GPT-3.5 ($0.0004)
- Moderate → GPT-4o-mini ($0.0008)
- Complex → GPT-4 ($0.0048)
- Critical → Claude Sonnet 4.5 ($0.0065)

## Environment Variables

```bash
# Required
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# Storage
AQE_STORAGE_MODE=development|testing|production
DATABASE_URL=postgresql://user:pass@localhost:5432/lionagi_qe

# Features
ENABLE_ROUTING=true
ENABLE_LEARNING=false
ROUTER_DEFAULT_MODEL=gpt-4o-mini
```

## Important Gotchas

1. **QEFleet is deprecated** - Use `QEOrchestrator` instead (removed in v2.0.0)
2. **Always await initialize()** - Before using orchestrator
3. **Memory namespace**: Agents share state via `aqe/*` prefix
4. **Fuzzy JSON parsing**: Enabled by default for LLM output robustness
5. **alcall retry**: Automatic exponential backoff on API failures

## Dependencies

Core: `lionagi>=0.18.2`, `pydantic>=2.8.0`, `fastapi>=0.109.0`, `asyncpg>=0.29.0`

Optional extras:
- `[dev]` - black, ruff, mypy, pytest-mock
- `[performance]` - locust, py-spy
- `[mcp]` - fastmcp, mcp
- `[persistence]` - redis
- `[api]` - uvicorn, websockets, python-jose
- `[all]` - Everything

## Testing Markers

```bash
pytest -m unit           # Fast unit tests
pytest -m integration    # Requires external services
pytest -m postgres       # Requires PostgreSQL
pytest -m redis          # Requires Redis
pytest -m slow           # Long-running tests
pytest -m e2e            # End-to-end tests
```

## Links

- Repository: https://github.com/lionagi/lionagi-qe-fleet
- LionAGI: https://github.com/khive-ai/lionagi
- Documentation: /docs/
- Examples: /examples/
