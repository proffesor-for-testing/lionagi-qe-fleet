"""QE Fleet specialized agents - 18 total agents"""

# Core Testing (6 agents)
from .test_generator import TestGeneratorAgent
from .test_executor import TestExecutorAgent
from .coverage_analyzer import CoverageAnalyzerAgent
from .quality_gate import QualityGateAgent
from .quality_analyzer import QualityAnalyzerAgent
from .code_complexity import CodeComplexityAnalyzerAgent

# Performance & Security (2 agents)
from .performance_tester import PerformanceTesterAgent
from .security_scanner import SecurityScannerAgent

# Strategic Planning (3 agents)
from .requirements_validator import RequirementsValidatorAgent
from .production_intelligence import ProductionIntelligenceAgent
from .fleet_commander import FleetCommanderAgent

# Advanced Testing (4 agents)
# NOTE: These agents have been fully implemented
from .regression_risk_analyzer import RegressionRiskAnalyzerAgent
from .test_data_architect import TestDataArchitectAgent
from .api_contract_validator import APIContractValidatorAgent
from .flaky_test_hunter import FlakyTestHunterAgent

# Specialized (3 agents)
from .deployment_readiness import DeploymentReadinessAgent
from .visual_tester import VisualTesterAgent
from .chaos_engineer import ChaosEngineerAgent

__all__ = [
    # Core Testing
    "TestGeneratorAgent",
    "TestExecutorAgent",
    "CoverageAnalyzerAgent",
    "QualityGateAgent",
    "QualityAnalyzerAgent",
    "CodeComplexityAnalyzerAgent",
    # Performance & Security
    "PerformanceTesterAgent",
    "SecurityScannerAgent",
    # Strategic Planning
    "RequirementsValidatorAgent",
    "ProductionIntelligenceAgent",
    "FleetCommanderAgent",
    # Advanced Testing
    "RegressionRiskAnalyzerAgent",
    "TestDataArchitectAgent",
    "APIContractValidatorAgent",
    "FlakyTestHunterAgent",
    # Specialized
    "DeploymentReadinessAgent",
    "VisualTesterAgent",
    "ChaosEngineerAgent",
]
