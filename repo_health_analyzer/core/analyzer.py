"""
Main repository analyzer orchestrating all analysis modules.

Coordinates git parsing, static analysis, ML prediction, and report generation.
"""

import time
from pathlib import Path
from typing import Optional, List, Any

from rich.console import Console

from .git_parser.repository import GitRepositoryParser
from .static_analyzer.code_quality import CodeQualityAnalyzer
from .static_analyzer.code_smells import CodeSmellDetector
from .static_analyzer.architecture import ArchitectureAnalyzer
from .test_analyzer.coverage import TestAnalyzer
from .docs_analyzer.documentation import DocumentationAnalyzer
from .ml.sustainability import SustainabilityPredictor
from ..models.report import HealthReport, OverallMetrics, AnalysisConfig
from ..visualization.generator import VisualizationGenerator


class RepositoryAnalyzer:
    """
    Main analyzer class that orchestrates all analysis modules.
    
    Performs comprehensive analysis of git repositories including:
    - Code quality metrics
    - Architecture analysis
    - Code smell detection
    - Test coverage analysis
    - Documentation quality
    - Sustainability prediction
    """
    
    def __init__(self, repo_path: Path, config: Optional[AnalysisConfig] = None, verbose: bool = False):
        self.repo_path = Path(repo_path)
        self.config = config or AnalysisConfig()
        self.verbose = verbose
        self.console = Console() if verbose else None
        
        # Initialize all analyzers
        self.git_parser = GitRepositoryParser(self.repo_path)
        self.code_quality_analyzer = CodeQualityAnalyzer(self.config)
        self.code_smell_detector = CodeSmellDetector(self.config)
        self.architecture_analyzer = ArchitectureAnalyzer(self.config)
        self.test_analyzer = TestAnalyzer(self.config)
        self.docs_analyzer = DocumentationAnalyzer(self.config)
        self.sustainability_predictor = SustainabilityPredictor(self.config)
        self.visualizer = VisualizationGenerator()
    
    def analyze(self) -> HealthReport:
        """
        Perform comprehensive repository analysis.
        
        Returns:
            HealthReport: Complete analysis results with metrics and recommendations
        """
        start_time = time.time()
        
        if self.verbose:
            self.console.print("[blue]Starting comprehensive repository analysis...[/blue]")
        
        # Step 1: Parse repository structure and git history
        if self.verbose:
            self.console.print("📁 Parsing repository structure and git history...")
        
        repo_info = self.git_parser.get_repository_info()
        source_files = self.git_parser.get_source_files(
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns
        )
        commit_history = self.git_parser.get_commit_history()
        
        # Step 2: Analyze code quality
        if self.verbose:
            self.console.print("🔍 Analyzing code quality metrics...")
        
        code_quality_metrics = self.code_quality_analyzer.analyze(source_files)
        
        # Step 3: Detect code smells
        if self.verbose:
            self.console.print("👃 Detecting code smells...")
        
        code_smell_metrics = self.code_smell_detector.analyze(source_files)
        
        # Step 4: Analyze architecture
        if self.verbose:
            self.console.print("🏗️ Analyzing architecture and dependencies...")
        
        architecture_metrics = self.architecture_analyzer.analyze(source_files)
        
        # Step 5: Analyze tests
        if self.verbose:
            self.console.print("🧪 Analyzing test coverage...")
        
        test_metrics = self.test_analyzer.analyze(self.repo_path, source_files)
        
        # Step 6: Analyze documentation
        if self.verbose:
            self.console.print("📚 Analyzing documentation quality...")
        
        docs_metrics = self.docs_analyzer.analyze(self.repo_path, source_files)
        
        # Step 7: Predict sustainability
        if self.verbose:
            self.console.print("🔮 Predicting repository sustainability...")
        
        sustainability_metrics = self.sustainability_predictor.analyze(
            commit_history, repo_info, source_files
        )
        
        # Step 8: Calculate overall score and generate recommendations
        if self.verbose:
            self.console.print("📊 Generating final report and recommendations...")
        
        overall_metrics = self._calculate_overall_metrics(
            code_quality_metrics,
            architecture_metrics,
            code_smell_metrics,
            test_metrics,
            docs_metrics,
            sustainability_metrics
        )
        
        recommendations = self._generate_recommendations(overall_metrics)
        
        analysis_duration = time.time() - start_time
        
        # Create final health report
        health_report = HealthReport(
            repository=repo_info,
            metrics=overall_metrics,
            recommendations=recommendations,
            analysis_duration=analysis_duration
        )
        
        if self.verbose:
            self.console.print(f"[green]✓ Analysis completed in {analysis_duration:.2f}s[/green]")
        
        return health_report
    
    def generate_visualizations(self, report: HealthReport) -> None:
        """Generate visualization files for the health report."""
        if self.verbose:
            self.console.print("🎨 Generating visualizations...")
        
        self.visualizer.generate_all(report, self.repo_path)
    
    def _calculate_overall_metrics(
        self,
        code_quality,
        architecture,
        code_smells,
        tests,
        docs,
        sustainability
    ) -> OverallMetrics:
        """Calculate overall score from individual metric scores."""
        
        # Weighted average of all scores
        weights = {
            'code_quality': 0.25,
            'architecture': 0.20,
            'code_smells': 0.15,  # Inverted - fewer smells = higher score
            'tests': 0.20,
            'docs': 0.10,
            'sustainability': 0.10
        }
        
        smell_score = max(0, 10 - code_smells.severity_score)
        
        overall_score = (
            code_quality.overall_score * weights['code_quality'] +
            architecture.score * weights['architecture'] +
            smell_score * weights['code_smells'] +
            tests.coverage_score * weights['tests'] +
            docs.score * weights['docs'] +
            sustainability.score * weights['sustainability']
        )
        
        return OverallMetrics(
            overall_score=round(overall_score, 1),
            code_quality=code_quality,
            architecture=architecture,
            code_smells=code_smells,
            tests=tests,
            documentation=docs,
            sustainability=sustainability
        )
    
    def _generate_recommendations(self, metrics: OverallMetrics) -> List[Any]:
        """Generate actionable recommendations based on analysis results."""
        from ..models.report import Recommendation, Priority
        
        recommendations = []
        
        # Code quality recommendations
        if metrics.code_quality.overall_score < 6:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Code Quality",
                description="Reduce cyclomatic complexity in complex functions",
                impact="Improves maintainability and reduces bugs",
                effort="medium"
            ))
        
        if metrics.code_quality.comment_density < 0.1:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Code Quality",
                description="Increase code documentation and comments",
                impact="Better code understanding for team members",
                effort="low"
            ))
        
        # Architecture recommendations
        if metrics.architecture.circular_dependencies > 0:
            recommendations.append(Recommendation(
                priority=Priority.CRITICAL,
                category="Architecture",
                description="Resolve circular dependencies between modules",
                impact="Prevents build issues and improves modularity",
                effort="high"
            ))
        
        if metrics.architecture.coupling_score > 7:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Architecture",
                description="Reduce coupling between modules",
                impact="Improves testability and maintainability",
                effort="medium"
            ))
        
        # Code smell recommendations
        if metrics.code_smells.total_count > 50:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Code Smells",
                description="Address high-priority code smells in hotspot files",
                impact="Reduces technical debt and improves code quality",
                effort="medium",
                files_affected=metrics.code_smells.hotspot_files[:5]
            ))
        
        # Test recommendations
        if metrics.tests.coverage_score < 7:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Testing",
                description="Increase test coverage, especially for critical modules",
                impact="Reduces bugs and improves confidence in changes",
                effort="high"
            ))
        
        if metrics.tests.test_to_source_ratio < 0.3:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Testing",
                description="Add more comprehensive test cases",
                impact="Better validation of functionality",
                effort="medium"
            ))
        
        # Documentation recommendations
        if metrics.documentation.score < 6:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Documentation",
                description="Improve API documentation and code comments",
                impact="Better onboarding and maintenance",
                effort="low"
            ))
        
        if not metrics.documentation.has_contributing_guide:
            recommendations.append(Recommendation(
                priority=Priority.LOW,
                category="Documentation",
                description="Add CONTRIBUTING.md guide for new contributors",
                impact="Easier contribution process",
                effort="low"
            ))
        
        # Sustainability recommendations
        if metrics.sustainability.score < 6:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Sustainability",
                description="Increase commit frequency and contributor diversity",
                impact="Ensures long-term project viability",
                effort="high"
            ))
        
        if metrics.sustainability.bus_factor < 3:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Sustainability",
                description="Reduce bus factor by spreading knowledge across team",
                impact="Reduces project risk",
                effort="medium"
            ))
        
        # Sort by priority
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        return recommendations
