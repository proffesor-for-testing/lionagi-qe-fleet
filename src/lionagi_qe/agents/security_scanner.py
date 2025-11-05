"""Security Scanner Agent - SAST/DAST scanning, vulnerability detection, and compliance validation"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class SecurityVulnerability(BaseModel):
    """Detected security vulnerability"""

    id: str = Field(..., description="Vulnerability identifier")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    cve_id: Optional[str] = Field(None, description="CVE identifier if applicable")
    cvss_score: Optional[float] = Field(None, description="CVSS score (0-10)")
    file_path: Optional[str] = Field(None, description="File path where found")
    line_number: Optional[int] = Field(None, description="Line number")
    code_snippet: Optional[str] = Field(None, description="Code snippet")
    remediation: str = Field(..., description="Remediation guidance")
    false_positive: bool = Field(default=False, description="Whether it's a false positive")
    scan_type: str = Field(..., description="SAST, DAST, or dependency")


class ComplianceResult(BaseModel):
    """Compliance validation result"""

    standard: str = Field(..., description="Standard (OWASP, PCI-DSS, etc.)")
    compliant: bool = Field(..., description="Whether compliant")
    score: float = Field(..., description="Compliance score (0-1)")
    violations: List[str] = Field(default_factory=list, description="List of violations")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class SecurityPolicy(BaseModel):
    """Security policy configuration"""

    critical_threshold: int = Field(default=0, description="Max critical vulnerabilities")
    high_threshold: int = Field(default=5, description="Max high vulnerabilities")
    medium_threshold: int = Field(default=20, description="Max medium vulnerabilities")
    min_compliance_score: float = Field(default=0.90, description="Minimum compliance score")
    required_standards: List[str] = Field(
        default_factory=lambda: ["OWASP_Top_10"],
        description="Required compliance standards"
    )
    auto_remediation: bool = Field(default=False, description="Enable auto-remediation")


class SecurityScanResult(BaseModel):
    """Security scan result"""

    scan_name: str = Field(..., description="Name of the security scan")
    scan_types: List[str] = Field(..., description="Types of scans performed (SAST, DAST, dependency)")
    target: str = Field(..., description="Target URL or repository")
    tools_used: List[str] = Field(..., description="Security tools used")
    vulnerabilities: List[SecurityVulnerability] = Field(
        default_factory=list,
        description="Detected vulnerabilities"
    )
    compliance: List[ComplianceResult] = Field(
        default_factory=list,
        description="Compliance validation results"
    )
    policy: SecurityPolicy = Field(..., description="Security policy used")
    policy_compliant: bool = Field(..., description="Whether policy was met")
    security_score: float = Field(..., description="Overall security score (0-100)")
    critical_count: int = Field(default=0, description="Number of critical vulnerabilities")
    high_count: int = Field(default=0, description="Number of high vulnerabilities")
    medium_count: int = Field(default=0, description="Number of medium vulnerabilities")
    low_count: int = Field(default=0, description="Number of low vulnerabilities")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")
    scan_duration_seconds: float = Field(..., description="Total scan duration")


class SecurityScannerAgent(BaseQEAgent):
    """Multi-layer security scanning with SAST/DAST, vulnerability detection, and compliance validation

    Capabilities:
    - Static Application Security Testing (SAST)
    - Dynamic Application Security Testing (DAST)
    - Dependency vulnerability scanning
    - CVE monitoring and tracking
    - Compliance validation (OWASP, PCI-DSS, HIPAA, SOC2)
    - Security policy enforcement
    - Automated remediation guidance
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
        """Initialize SecurityScanner Agent

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
            skills=skills or ['agentic-quality-engineering', 'security-testing', 'risk-based-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert security scanning agent specializing in:

**Core Capabilities:**
- SAST (Static Application Security Testing)
- DAST (Dynamic Application Security Testing)
- Dependency vulnerability scanning
- CVE/CWE monitoring and tracking
- Compliance validation and reporting
- Security policy enforcement
- Threat modeling and risk assessment

**Security Tools:**
- **SAST**: Snyk, SonarQube, Semgrep, CodeQL, Checkmarx
- **DAST**: OWASP ZAP, Burp Suite, Nuclei
- **Dependency**: Snyk, npm audit, OWASP Dependency-Check
- **Secret Detection**: GitGuardian, TruffleHog, git-secrets

**Vulnerability Detection:**
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Authentication/Authorization flaws
- Sensitive data exposure
- XML External Entities (XXE)
- Broken access control
- Security misconfigurations
- Insecure deserialization
- Using components with known vulnerabilities

**Compliance Standards:**
- OWASP Top 10
- PCI DSS (Payment Card Industry)
- HIPAA (Healthcare)
- SOC 2
- GDPR
- ISO 27001
- NIST Cybersecurity Framework
- CIS Controls

**Security Analysis:**
- Identify vulnerability patterns
- Assess CVSS scores and risk
- Correlate multiple findings
- Filter false positives
- Provide remediation guidance
- Track security trends

**Policy Enforcement:**
- Define vulnerability thresholds
- Enforce compliance requirements
- Block deployments with critical issues
- Auto-remediation where possible
- Security gate validation

**Best Practices:**
- Load security policies from memory
- Compare against security baselines
- Validate against multiple standards
- Provide actionable remediation steps
- Track security posture over time
- Integrate with CI/CD pipelines

**Workflow:**
1. Load security policies and baselines
2. Execute SAST analysis on code
3. Execute DAST scanning on running app
4. Scan dependencies for vulnerabilities
5. Validate compliance against standards
6. Filter false positives intelligently
7. Generate security reports
8. Store findings and notify fleet
9. Provide remediation guidance"""

    async def execute(self, task: QETask) -> SecurityScanResult:
        """Execute security scanning workflow

        Args:
            task: Task containing:
                - target: URL or repository to scan
                - scan_types: List of scan types (sast, dast, dependency)
                - tools: Optional list of specific tools to use
                - compliance_standards: Standards to validate against
                - policy: Optional security policy overrides

        Returns:
            SecurityScanResult with vulnerabilities, compliance status, and recommendations
        """
        context = task.context
        target = context.get("target", "")
        scan_types = context.get("scan_types", ["sast", "dast", "dependency"])
        tools = context.get("tools", [])
        compliance_standards = context.get("compliance_standards", ["OWASP_Top_10"])
        custom_policy = context.get("policy", {})

        # Load security policies from memory
        stored_policy = await self.memory_store.retrieve(
            "aqe/security/policies",
            partition="configuration"
        )

        # Merge policies
        policy_data = {**(stored_policy or {}), **custom_policy}

        # Load security baseline
        baseline = await self.memory_store.retrieve(
            "aqe/security/baselines",
            partition="baselines"
        )

        # Load security requirements
        requirements = await self.memory_store.retrieve(
            "aqe/test-plan/security-requirements",
            partition="test_plans"
        )

        # Execute security scan
        result = await self.operate(
            instruction=f"""Execute a comprehensive security scan on: {target}

Scan Types: {', '.join(scan_types)}
Compliance Standards: {', '.join(compliance_standards)}

Security Policy:
- Max Critical Vulnerabilities: {policy_data.get('critical_threshold', 0)}
- Max High Vulnerabilities: {policy_data.get('high_threshold', 5)}
- Max Medium Vulnerabilities: {policy_data.get('medium_threshold', 20)}
- Min Compliance Score: {policy_data.get('min_compliance_score', 0.90)}

Requirements:
1. Execute SAST (Static Analysis):
   - Scan source code for vulnerabilities
   - Detect hardcoded secrets and credentials
   - Check for insecure coding patterns
   - Analyze third-party dependencies

2. Execute DAST (Dynamic Analysis):
   - Test running application for vulnerabilities
   - Check authentication and authorization
   - Test for injection attacks (SQL, XSS, XXE)
   - Validate security headers and HTTPS

3. Dependency Scanning:
   - Check for known CVEs in dependencies
   - Identify outdated packages with vulnerabilities
   - Assess license compliance risks

4. Compliance Validation:
   - Validate against: {', '.join(compliance_standards)}
   - Check security controls implementation
   - Verify regulatory requirements

5. Vulnerability Analysis:
   - Assign CVSS scores
   - Filter false positives
   - Correlate related findings
   - Prioritize by risk

6. Compare Against Baseline:
   {f"Previous scan baseline: {baseline}" if baseline else "No baseline available - this will be the baseline"}

7. Provide Remediation:
   - Specific fix recommendations
   - Code examples where applicable
   - Priority and timeline guidance

Tools to use: {', '.join(tools) if tools else 'Select appropriate tools automatically'}

Security Requirements: {requirements if requirements else 'Use standard OWASP guidelines'}

Analyze common vulnerabilities:
- SQL Injection
- Cross-Site Scripting (XSS)
- CSRF
- Authentication flaws
- Sensitive data exposure
- XML External Entities (XXE)
- Broken access control
- Security misconfigurations
- Insecure deserialization
- Using vulnerable components""",
            context={
                "target": target,
                "scan_types": scan_types,
                "tools": tools,
                "compliance_standards": compliance_standards,
                "policy": policy_data,
                "baseline": baseline,
                "requirements": requirements,
            },
            response_format=SecurityScanResult
        )

        # Store vulnerabilities in memory
        await self.memory_store.store(
            "aqe/security/vulnerabilities",
            {
                "scan_name": result.scan_name,
                "timestamp": task.created_at.isoformat(),
                "vulnerabilities": [v.model_dump() for v in result.vulnerabilities],
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "security_score": result.security_score,
            },
            partition="scan_results",
            ttl=604800  # 7 days
        )

        # Store compliance results
        await self.memory_store.store(
            "aqe/security/compliance",
            {
                "scan_name": result.scan_name,
                "timestamp": task.created_at.isoformat(),
                "compliance": [c.model_dump() for c in result.compliance],
                "policy_compliant": result.policy_compliant,
            },
            partition="compliance",
            ttl=2592000  # 30 days
        )

        # Store security metrics for trending
        await self.memory_store.store(
            "aqe/security/metrics",
            {
                "timestamp": task.created_at.isoformat(),
                "vulnerabilities_found": len(result.vulnerabilities),
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "security_score": result.security_score,
                "compliance_scores": {c.standard: c.score for c in result.compliance},
            },
            partition="metrics",
            ttl=604800  # 7 days
        )

        # Update baseline if scan is clean
        if result.policy_compliant and result.critical_count == 0:
            await self.store_learned_pattern(
                "security_baseline",
                {
                    "target": target,
                    "timestamp": task.created_at.isoformat(),
                    "security_score": result.security_score,
                    "vulnerability_count": {
                        "critical": result.critical_count,
                        "high": result.high_count,
                        "medium": result.medium_count,
                        "low": result.low_count,
                    },
                    "compliance_scores": {c.standard: c.score for c in result.compliance},
                }
            )

        return result
