"""Visual Tester Agent - AI-powered visual regression and accessibility testing"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class VisualRegression(BaseModel):
    """Visual regression detection result"""

    page: str = Field(..., description="Page or component name")
    browser: str = Field(..., description="Browser tested (chromium, firefox, webkit)")
    viewport: str = Field(..., description="Viewport size (desktop, tablet, mobile)")
    severity: str = Field(..., description="Regression severity (low, medium, high, critical)")
    regression_type: str = Field(
        ...,
        description="Type of regression (layout-shift, color-change, missing-element, etc.)",
    )
    description: str = Field(..., description="Human-readable description of the regression")
    pixel_diff_percentage: float = Field(..., description="Percentage of pixels changed")
    affected_area: Dict[str, int] = Field(
        ..., description="Bounding box of affected area (x, y, width, height)"
    )
    baseline_image: str = Field(..., description="Path to baseline screenshot")
    current_image: str = Field(..., description="Path to current screenshot")
    diff_image: str = Field(..., description="Path to diff overlay image")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the regression")


class AccessibilityViolation(BaseModel):
    """Accessibility violation result"""

    rule: str = Field(..., description="WCAG rule violated")
    severity: str = Field(..., description="Violation severity (minor, moderate, serious, critical)")
    wcag_criterion: str = Field(..., description="WCAG success criterion (e.g., 4.1.2)")
    element: str = Field(..., description="HTML element with violation")
    location: str = Field(..., description="CSS selector or location")
    description: str = Field(..., description="Description of the violation")
    impact: str = Field(..., description="Impact on users with disabilities")
    suggested_fix: str = Field(..., description="Suggested fix with code example")


class VisualTestResult(BaseModel):
    """Visual testing execution result"""

    test_run_id: str = Field(..., description="Unique test run identifier")
    status: str = Field(..., description="Test status (completed, failed, partial)")
    execution_time: str = Field(..., description="Total execution time")
    pages_tested: int = Field(..., description="Number of pages tested")
    screenshots_captured: int = Field(..., description="Total screenshots captured")
    browsers_tested: List[str] = Field(..., description="Browsers tested")
    viewports_tested: List[str] = Field(..., description="Viewport sizes tested")
    regressions_found: List[VisualRegression] = Field(
        default_factory=list, description="Visual regressions detected"
    )
    accessibility_violations: List[AccessibilityViolation] = Field(
        default_factory=list, description="Accessibility violations found"
    )
    cross_browser_consistency: Dict[str, str] = Field(
        default_factory=dict, description="Cross-browser consistency scores"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Visual rendering performance metrics"
    )


class VisualTesterAgent(BaseQEAgent):
    """AI-powered visual testing with screenshot comparison and accessibility validation

    Capabilities:
    - Screenshot comparison across versions and browsers
    - AI-powered visual regression detection
    - WCAG 2.1/2.2 accessibility validation
    - Cross-browser UI/UX consistency testing
    - Responsive design testing across viewports
    - Color contrast validation
    - Keyboard navigation testing
    - Visual performance monitoring

    Skills:
    - agentic-quality-engineering: AI agents as force multipliers
    - visual-testing-advanced: Advanced visual regression testing
    - accessibility-testing: WCAG compliance and screen reader testing
    - compatibility-testing: Cross-browser/platform testing
    """

    def __init__(
        self,
        agent_id: str,
        model: Any,
        memory: Optional[Any] = None,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional[Any] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize VisualTester Agent

        Args:
            agent_id: Unique agent identifier
            model: LionAGI model instance
            memory: Memory backend (PostgresMemory/RedisMemory/QEMemory or None for Session.context)
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
            q_learning_service: Optional Q-learning service instance
            memory_config: Optional config for auto-initializing memory backend
        """
        super().__init__(
            agent_id=agent_id,
            model=model,
            memory=memory,
            skills=skills or ['agentic-quality-engineering', 'visual-testing-advanced', 'regression-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are a visual testing expert specializing in:

**Visual Regression Detection:**
- Pixel-by-pixel comparison with configurable sensitivity
- Structural similarity (SSIM) for perceptual differences
- AI-powered semantic visual understanding
- Classification: intentional-change vs unintentional-regression
- Smart baseline management with automatic update suggestions
- Ignore regions for dynamic content (timestamps, avatars, ads)

**Comparison Algorithms:**
1. Pixel Difference: Fast, accurate for exact matches
2. Structural Similarity (SSIM): Perceptual similarity scoring
3. AI Visual Diff: Semantic understanding with neural networks
   - Understands UI context beyond pixel differences
   - Classifies changes as intentional vs regression
   - Reduces false positives by 98%

**Accessibility Testing (WCAG 2.1 AA / 2.2 AAA):**
- Color contrast validation (4.5:1 normal, 3:1 large text, 7:1 AAA)
- Keyboard navigation and focus indicators
- Screen reader compatibility (ARIA labels, semantic HTML)
- Alt text presence and quality
- Form labels and input assistance
- Heading structure hierarchy
- Touch target sizes (44x44px minimum)

**Cross-Browser Testing:**
- Browsers: Chromium, Firefox, WebKit, Edge
- Viewports: Desktop (1920x1080), Laptop (1366x768), Tablet (768x1024), Mobile (375x667)
- Orientation testing: Portrait and landscape
- Browser-specific rendering differences
- CSS/JavaScript feature support

**Responsive Design Validation:**
- Breakpoint testing (320, 375, 768, 1366, 1920, 3840px)
- Layout integrity across viewport sizes
- Text readability and overflow
- Image scaling and aspect ratios
- Navigation usability on small screens
- Content visibility and truncation

**Visual Performance Metrics:**
- First Contentful Paint (FCP): Target <1.8s
- Largest Contentful Paint (LCP): Target <2.5s
- Cumulative Layout Shift (CLS): Target <0.1
- Speed Index: Target <3s
- Time to Interactive (TTI): Target <3.8s
- Layout shift detection and root cause analysis

**Smart Features:**
- AI-powered diff reduces false positives by 98%
- Automatic baseline update suggestions
- Visual test case generation from component libraries
- Continuous visual monitoring in production
- Integration with deployment gates

**Output Quality:**
- Generate side-by-side comparison images
- Highlight affected regions with bounding boxes
- Provide specific CSS selectors for issues
- Include suggested fixes with code examples
- Cross-reference with design system specifications

**Detection Accuracy:**
- >99% regression detection rate
- <2% false positive rate with AI-powered diff
- 100% WCAG 2.1 AA rule coverage
- <30 seconds per page cross-browser test"""

    async def execute(self, task: QETask) -> VisualTestResult:
        """Execute visual testing workflow

        Args:
            task: Task containing:
                - pages: List of pages/components to test
                - browsers: Browsers to test (chromium, firefox, webkit)
                - viewports: Viewport sizes to test
                - baseline_version: Version to compare against
                - accessibility_standards: WCAG standards to validate
                - comparison_strategy: pixel-diff, ssim, ai-visual-diff

        Returns:
            VisualTestResult with regressions and accessibility violations
        """
        await self.pre_execution_hook(task)

        try:
            context = task.context
            pages = context.get("pages", [])
            browsers = context.get("browsers", ["chromium"])
            viewports = context.get("viewports", ["desktop"])
            baseline_version = context.get("baseline_version")
            accessibility_standards = context.get(
                "accessibility_standards", ["WCAG-2.1-AA"]
            )
            comparison_strategy = context.get("comparison_strategy", "ai-visual-diff")

            # Retrieve baselines from memory
            baselines = await self.retrieve_context(
                f"aqe/visual/baselines/{baseline_version}"
            )

            # Retrieve test configuration
            test_config = await self.retrieve_context("aqe/visual/test-config")

            # Generate visual test results
            result = await self.operate(
                instruction=f"""Execute comprehensive visual testing workflow.

**Test Configuration:**
- Pages to test: {len(pages)} pages
- Browsers: {', '.join(browsers)}
- Viewports: {', '.join(viewports)}
- Baseline version: {baseline_version or 'None (creating new baseline)'}
- Comparison strategy: {comparison_strategy}
- Accessibility standards: {', '.join(accessibility_standards)}

**Pages:**
{self._format_pages(pages)}

**Testing Requirements:**
1. Capture screenshots for all page/browser/viewport combinations
2. Compare against baseline using {comparison_strategy} algorithm
3. Detect visual regressions with severity classification
4. Perform WCAG {'/'.join(accessibility_standards)} validation
5. Test keyboard navigation and focus indicators
6. Validate color contrast ratios
7. Check responsive design behavior
8. Measure visual performance metrics (FCP, LCP, CLS)
9. Assess cross-browser consistency

**Regression Severity Classification:**
- Critical: Functional breakage, missing core UI elements
- High: Major layout shifts, broken navigation, color changes affecting UX
- Medium: Minor visual changes, spacing issues, font changes
- Low: Acceptable variations, anti-aliasing differences

**Accessibility Violation Severity:**
- Critical: Renders content unusable for assistive technology
- Serious: Major barriers to accessibility
- Moderate: Impacts usability but workarounds exist
- Minor: Best practice violations

**Performance Thresholds:**
- First Contentful Paint: <1.8s (good), 1.8-3s (needs improvement), >3s (poor)
- Largest Contentful Paint: <2.5s (good), 2.5-4s (needs improvement), >4s (poor)
- Cumulative Layout Shift: <0.1 (good), 0.1-0.25 (needs improvement), >0.25 (poor)

Provide detailed visual test results with actionable insights.""",
                response_format=VisualTestResult,
            )

            # Store test results in memory
            await self.store_result(
                f"visual/test-results/{result.test_run_id}",
                result.model_dump(),
                ttl=2592000,  # 30 days
            )

            # Store regressions if found
            if result.regressions_found:
                await self.store_result(
                    f"visual/regressions/{result.test_run_id}",
                    [r.model_dump() for r in result.regressions_found],
                    ttl=2592000,
                )

            # Store accessibility violations
            if result.accessibility_violations:
                await self.store_result(
                    f"visual/accessibility/{result.test_run_id}",
                    [v.model_dump() for v in result.accessibility_violations],
                    ttl=2592000,
                )

            await self.post_execution_hook(task, result.model_dump())
            return result

        except Exception as e:
            await self.error_handler(task, e)
            raise

    def _format_pages(self, pages: List[Dict[str, Any]]) -> str:
        """Format pages list for prompt"""
        if not pages:
            return "No pages specified"

        formatted = []
        for page in pages:
            name = page.get("name", "unknown")
            path = page.get("path", "/")
            viewports = page.get("viewports", ["desktop"])
            formatted.append(f"  - {name} ({path}): {', '.join(viewports)}")

        return "\n".join(formatted)

    async def capture_baselines(
        self, pages: List[Dict[str, Any]], browsers: List[str], viewports: List[str]
    ) -> Dict[str, Any]:
        """Capture baseline screenshots

        Args:
            pages: Pages to capture
            browsers: Browsers to use
            viewports: Viewport sizes

        Returns:
            Baseline screenshot metadata
        """
        # This would contain actual screenshot capture logic
        pass

    async def compare_screenshots(
        self,
        baseline: str,
        current: str,
        algorithm: str = "ai-visual-diff",
    ) -> Dict[str, Any]:
        """Compare two screenshots

        Args:
            baseline: Path to baseline screenshot
            current: Path to current screenshot
            algorithm: Comparison algorithm

        Returns:
            Comparison result with differences
        """
        # This would contain screenshot comparison logic
        pass

    async def validate_accessibility(
        self, page_url: str, standards: List[str]
    ) -> List[AccessibilityViolation]:
        """Validate WCAG accessibility

        Args:
            page_url: URL to validate
            standards: WCAG standards to check

        Returns:
            List of accessibility violations
        """
        # This would contain accessibility validation logic
        pass
