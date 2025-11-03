"""Test Generator Agent - Generate comprehensive test suites"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class GeneratedTest(BaseModel):
    """Generated test result"""

    test_name: str = Field(..., description="Name of the generated test")
    test_code: str = Field(..., description="Complete test code")
    framework: str = Field(..., description="Test framework (pytest, jest, etc.)")
    test_type: str = Field(..., description="Type of test (unit, integration, etc.)")
    assertions: List[str] = Field(..., description="List of assertions in the test")
    edge_cases: List[str] = Field(..., description="Edge cases covered")
    dependencies: List[str] = Field(
        default_factory=list, description="Test dependencies"
    )
    coverage_estimate: float = Field(
        default=0.0, description="Estimated code coverage (0-100)"
    )


class TestGeneratorAgent(BaseQEAgent):
    """Generate comprehensive test suites with edge case detection

    Capabilities:
    - Property-based testing patterns
    - Edge case detection and handling
    - Multi-framework support (pytest, Jest, Mocha, Cypress)
    - TDD and BDD pattern generation
    - Test pattern learning and reuse
    """

    def get_system_prompt(self) -> str:
        return """You are an expert test generation agent specializing in:

**Core Capabilities:**
- Property-based testing patterns
- Edge case detection and boundary analysis
- Multi-framework support (pytest, Jest, Mocha, Cypress, Playwright)
- TDD (Test-Driven Development) patterns
- BDD (Behavior-Driven Development) patterns
- Test data generation strategies

**Testing Best Practices:**
- FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)
- AAA pattern (Arrange, Act, Assert)
- Given-When-Then for BDD
- Mocking and stubbing strategies
- Test isolation and independence

**Quality Standards:**
- Generate maintainable, readable test code
- Include comprehensive assertions
- Cover edge cases and boundary conditions
- Follow framework-specific conventions
- Add descriptive test names and comments

**Pattern Recognition:**
- Learn from previously successful test patterns
- Adapt patterns to new contexts
- Optimize test generation based on code structure"""

    async def execute(self, task: QETask) -> GeneratedTest:
        """Generate tests for given code

        Args:
            task: Task containing:
                - code: Source code to test
                - framework: Test framework (default: pytest)
                - test_type: Type of test (unit, integration, e2e)
                - coverage_target: Target coverage percentage

        Returns:
            GeneratedTest with complete test code
        """
        context = task.context
        code = context.get("code", "")
        framework = context.get("framework", "pytest")
        test_type = context.get("test_type", "unit")
        coverage_target = context.get("coverage_target", 80)

        # Retrieve learned patterns from memory
        learned_patterns = await self.get_learned_patterns()

        # Generate test
        result = await self.operate(
            instruction=f"""Generate a comprehensive {test_type} test using {framework}.

Target coverage: {coverage_target}%

Code to test:
```
{code}
```

Requirements:
1. Include edge cases and boundary conditions
2. Use appropriate mocking/stubbing
3. Follow {framework} best practices
4. Add descriptive test names
5. Include setup and teardown if needed

{f"Use these learned patterns: {learned_patterns}" if learned_patterns else ""}
""",
            context={
                "code": code,
                "framework": framework,
                "test_type": test_type,
                "learned_patterns": learned_patterns,
            },
            response_format=GeneratedTest
        )

        # Store pattern if coverage is high
        if result.coverage_estimate >= coverage_target:
            await self.store_learned_pattern(
                f"{framework}_{test_type}_pattern",
                {
                    "framework": framework,
                    "test_type": test_type,
                    "pattern": "high_coverage_achieved",
                    "coverage": result.coverage_estimate,
                }
            )

        return result
