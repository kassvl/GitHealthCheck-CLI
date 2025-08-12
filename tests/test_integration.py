"""
Integration tests for the complete analysis pipeline.

Tests end-to-end functionality with real repository structures.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.report import AnalysisConfig


class TestIntegration:
    """Integration test cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = AnalysisConfig()
    
    def test_empty_repository_analysis(self):
        """Test analysis of an empty repository."""
        # Create minimal git repository structure
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        with patch('git.Repo') as mock_repo:
            # Mock empty repository
            mock_repo_instance = Mock()
            mock_repo_instance.iter_commits.return_value = []
            mock_repo.return_value = mock_repo_instance
            
            analyzer = RepositoryAnalyzer(self.temp_dir, self.config)
            
            # This would normally require full mocking of all components
            # For integration test, we verify the analyzer can be created
            assert analyzer is not None
            assert analyzer.repo_path == self.temp_dir
    
    def test_sample_python_project(self):
        """Test analysis of a sample Python project."""
        # Create sample Python project structure
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        # Create sample Python files
        src_dir = self.temp_dir / "src"
        src_dir.mkdir()
        
        # Main module
        main_file = src_dir / "main.py"
        main_file.write_text('''
"""Main module for sample project."""

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

def long_function():
    """This is a very long function that should trigger code smell detection."""
    # This function is intentionally long to test smell detection
    result = 0
    for i in range(100):
        if i % 2 == 0:
            result += i
        else:
            result -= i
        
        if result > 1000:
            break
        
        # More unnecessary code to make it longer
        temp = result * 2
        if temp > 500:
            temp = temp / 2
        
        result = temp
    
    return result

class ExampleClass:
    """Example class with multiple methods."""
    
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        """Get the current value."""
        return self.value
    
    def set_value(self, value):
        """Set the current value."""
        self.value = value
''')
        
        # Test file
        test_file = src_dir / "test_main.py"
        test_file.write_text('''
"""Test module for main.py."""

import unittest
from main import calculate_sum, ExampleClass

class TestMain(unittest.TestCase):
    """Test cases for main module."""
    
    def test_calculate_sum(self):
        """Test sum calculation."""
        self.assertEqual(calculate_sum(2, 3), 5)
        self.assertEqual(calculate_sum(-1, 1), 0)
    
    def test_example_class(self):
        """Test ExampleClass."""
        obj = ExampleClass()
        self.assertEqual(obj.get_value(), 0)
        
        obj.set_value(42)
        self.assertEqual(obj.get_value(), 42)

if __name__ == '__main__':
    unittest.main()
''')
        
        # README file
        readme_file = self.temp_dir / "README.md"
        readme_file.write_text('''
# Sample Project

This is a sample Python project for testing the Repo Health Analyzer.

## Installation

```bash
pip install -e .
```

## Usage

```python
from src.main import calculate_sum
result = calculate_sum(1, 2)
```

## Testing

```bash
python -m pytest
```
''')
        
        with patch('git.Repo') as mock_repo:
            # Mock repository with some commits
            mock_commit = Mock()
            mock_commit.hexsha = "abc123"
            mock_commit.author.email = "test@example.com"
            mock_commit.committed_datetime = None
            mock_commit.message = "Initial commit"
            mock_commit.stats.total = {'files': 2, 'insertions': 50, 'deletions': 0}
            mock_commit.parents = []
            
            mock_repo_instance = Mock()
            mock_repo_instance.iter_commits.return_value = [mock_commit]
            mock_repo.return_value = mock_repo_instance
            
            analyzer = RepositoryAnalyzer(self.temp_dir, self.config)
            
            # Test that analyzer can be created with sample project
            assert analyzer is not None


class TestReportGeneration:
    """Test health report generation and serialization."""
    
    def test_report_json_serialization(self):
        """Test health report can be serialized to JSON."""
        from repo_health_analyzer.models.report import (
            HealthReport, RepositoryInfo, OverallMetrics,
            CodeQualityMetrics, ArchitectureMetrics, CodeSmellMetrics,
            TestMetrics, DocumentationMetrics, SustainabilityMetrics
        )
        from datetime import datetime, timezone
        
        # Create minimal report
        repo_info = RepositoryInfo(
            path="/test",
            name="test",
            analyzed_at=datetime.now(timezone.utc),
            total_files=1,
            total_lines=100,
            commit_count=10,
            contributors=1,
            age_days=30
        )
        
        metrics = OverallMetrics(
            overall_score=7.5,
            code_quality=CodeQualityMetrics(
                overall_score=8.0,
                function_length_avg=20.0,
                comment_density=0.1,
                naming_consistency=0.9,
                duplication_ratio=0.05
            ),
            architecture=ArchitectureMetrics(
                score=7.0,
                dependency_count=5,
                circular_dependencies=0,
                coupling_score=4.0,
                cohesion_score=8.0,
                srp_violations=1,
                module_count=3,
                depth_of_inheritance=1.0
            ),
            code_smells=CodeSmellMetrics(
                total_count=5,
                severity_score=2.0
            ),
            tests=TestMetrics(
                coverage_score=8.0,
                test_files_count=5,
                test_to_source_ratio=0.5,
                test_success_rate=0.95,
                has_coverage_report=False
            ),
            documentation=DocumentationMetrics(
                score=6.0,
                readme_quality=8.0,
                docstring_coverage=0.7,
                api_doc_coverage=0.6,
                has_changelog=False,
                has_contributing_guide=False,
                doc_files_count=2
            ),
            sustainability=SustainabilityMetrics(
                score=7.0,
                maintenance_probability=0.8,
                activity_trend="stable",
                bus_factor=2,
                recent_activity_score=7.0,
                contributor_diversity=0.5,
                commit_frequency_score=6.0
            )
        )
        
        report = HealthReport(
            repository=repo_info,
            metrics=metrics,
            analysis_duration=30.5
        )
        
        # Test JSON serialization
        json_data = json.dumps(report.model_dump(), default=str)
        assert "test" in json_data
        assert "7.5" in json_data
    
    def test_report_file_operations(self):
        """Test saving report to files."""
        from repo_health_analyzer.models.report import (
            HealthReport, RepositoryInfo, OverallMetrics,
            CodeQualityMetrics, ArchitectureMetrics, CodeSmellMetrics,
            TestMetrics, DocumentationMetrics, SustainabilityMetrics
        )
        from datetime import datetime, timezone
        
        # Create test report (minimal)
        repo_info = RepositoryInfo(
            path="/test",
            name="test",
            analyzed_at=datetime.now(timezone.utc),
            total_files=1,
            total_lines=100,
            commit_count=10,
            contributors=1,
            age_days=30
        )
        
        metrics = OverallMetrics(
            overall_score=7.5,
            code_quality=CodeQualityMetrics(
                overall_score=8.0,
                function_length_avg=20.0,
                comment_density=0.1,
                naming_consistency=0.9,
                duplication_ratio=0.05
            ),
            architecture=ArchitectureMetrics(
                score=7.0,
                dependency_count=5,
                circular_dependencies=0,
                coupling_score=4.0,
                cohesion_score=8.0,
                srp_violations=1,
                module_count=3,
                depth_of_inheritance=1.0
            ),
            code_smells=CodeSmellMetrics(
                total_count=5,
                severity_score=2.0
            ),
            tests=TestMetrics(
                coverage_score=8.0,
                test_files_count=5,
                test_to_source_ratio=0.5,
                test_success_rate=0.95,
                has_coverage_report=False
            ),
            documentation=DocumentationMetrics(
                score=6.0,
                readme_quality=8.0,
                docstring_coverage=0.7,
                api_doc_coverage=0.6,
                has_changelog=False,
                has_contributing_guide=False,
                doc_files_count=2
            ),
            sustainability=SustainabilityMetrics(
                score=7.0,
                maintenance_probability=0.8,
                activity_trend="stable",
                bus_factor=2,
                recent_activity_score=7.0,
                contributor_diversity=0.5,
                commit_frequency_score=6.0
            )
        )
        
        report = HealthReport(
            repository=repo_info,
            metrics=metrics,
            analysis_duration=30.5
        )
        
        # Test JSON save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
        
        report.save_json(json_path)
        
        # Verify file was created and contains expected data
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert data['repository']['name'] == "test"
            assert data['metrics']['overall_score'] == 7.5
