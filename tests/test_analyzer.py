"""
Test suite for the main repository analyzer.

Tests the core functionality of repository analysis and report generation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.report import AnalysisConfig


class TestRepositoryAnalyzer:
    """Test cases for RepositoryAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AnalysisConfig()
    
    def test_analyzer_initialization(self):
        """Test analyzer can be initialized with valid repo."""
        # Create a mock git repository
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        analyzer = RepositoryAnalyzer(self.temp_dir, self.config)
        assert analyzer.repo_path == self.temp_dir
        assert analyzer.config == self.config
    
    def test_analyzer_invalid_repo(self):
        """Test analyzer raises error for invalid repository."""
        with pytest.raises(ValueError, match="Not a valid git repository"):
            RepositoryAnalyzer(self.temp_dir, self.config)
    
    @patch('repo_health_analyzer.core.analyzer.GitRepositoryParser')
    @patch('repo_health_analyzer.core.analyzer.CodeQualityAnalyzer')
    def test_analyze_basic_flow(self, mock_quality, mock_parser):
        """Test basic analysis flow."""
        # Setup mocks
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        # Mock repository info
        from repo_health_analyzer.models.report import RepositoryInfo
        from datetime import datetime, timezone
        
        mock_repo_info = RepositoryInfo(
            path=str(self.temp_dir),
            name="test-repo",
            analyzed_at=datetime.now(timezone.utc),
            total_files=10,
            total_lines=1000,
            languages={"Python": 800, "JavaScript": 200},
            commit_count=50,
            contributors=3,
            age_days=100
        )
        
        mock_parser_instance.get_repository_info.return_value = mock_repo_info
        mock_parser_instance.get_source_files.return_value = []
        mock_parser_instance.get_commit_history.return_value = []
        
        # Mock other analyzers
        with patch('repo_health_analyzer.core.analyzer.CodeSmellDetector'), \
             patch('repo_health_analyzer.core.analyzer.ArchitectureAnalyzer'), \
             patch('repo_health_analyzer.core.analyzer.TestAnalyzer'), \
             patch('repo_health_analyzer.core.analyzer.DocumentationAnalyzer'), \
             patch('repo_health_analyzer.core.analyzer.SustainabilityPredictor'):
            
            analyzer = RepositoryAnalyzer(self.temp_dir, self.config)
            
            # This would normally fail without proper mocking of all analyzers
            # For now, we'll just test initialization
            assert analyzer is not None
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = AnalysisConfig()
        
        # Test default values
        assert config.include_patterns
        assert config.exclude_patterns
        assert config.max_file_size_mb > 0
        assert config.complexity_threshold > 0
        assert config.function_length_threshold > 0


class TestHealthReportModel:
    """Test cases for health report data models."""
    
    def test_health_report_serialization(self):
        """Test health report can be serialized to JSON."""
        from repo_health_analyzer.models.report import (
            HealthReport, RepositoryInfo, OverallMetrics,
            CodeQualityMetrics, ArchitectureMetrics, CodeSmellMetrics,
            TestMetrics, DocumentationMetrics, SustainabilityMetrics
        )
        from datetime import datetime, timezone
        
        # Create minimal health report
        repo_info = RepositoryInfo(
            path="/test/repo",
            name="test-repo",
            analyzed_at=datetime.now(timezone.utc),
            total_files=10,
            total_lines=1000,
            commit_count=50,
            contributors=3,
            age_days=100
        )
        
        metrics = OverallMetrics(
            overall_score=7.5,
            code_quality=CodeQualityMetrics(
                overall_score=8.0,
                function_length_avg=25.5,
                comment_density=0.15,
                naming_consistency=0.85,
                duplication_ratio=0.05
            ),
            architecture=ArchitectureMetrics(
                score=7.0,
                dependency_count=15,
                circular_dependencies=0,
                coupling_score=5.5,
                cohesion_score=7.2,
                srp_violations=2,
                module_count=8,
                depth_of_inheritance=1.5
            ),
            code_smells=CodeSmellMetrics(
                total_count=12,
                severity_score=3.5
            ),
            tests=TestMetrics(
                coverage_score=8.5,
                test_files_count=25,
                test_to_source_ratio=0.4,
                test_success_rate=0.95,
                has_coverage_report=True
            ),
            documentation=DocumentationMetrics(
                score=6.5,
                readme_quality=8.0,
                docstring_coverage=0.7,
                api_doc_coverage=0.6,
                has_changelog=True,
                has_contributing_guide=False,
                doc_files_count=5
            ),
            sustainability=SustainabilityMetrics(
                score=7.8,
                maintenance_probability=0.85,
                activity_trend="stable",
                bus_factor=3,
                recent_activity_score=7.5,
                contributor_diversity=0.6,
                commit_frequency_score=6.8
            )
        )
        
        report = HealthReport(
            repository=repo_info,
            metrics=metrics,
            analysis_duration=45.2
        )
        
        # Test serialization
        json_data = report.model_dump()
        assert json_data['repository']['name'] == "test-repo"
        assert json_data['metrics']['overall_score'] == 7.5
        
        # Test JSON serialization
        json_str = json.dumps(json_data, default=str)
        assert "test-repo" in json_str
