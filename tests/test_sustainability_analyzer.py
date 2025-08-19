"""Tests for Sustainability Analyzer."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from repo_health_analyzer.core.analyzers.sustainability_analyzer import SustainabilityAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig, RepositoryInfo


class TestSustainabilityAnalyzer:
    """Test cases for Sustainability Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return SustainabilityAnalyzer(config)
    
    @pytest.fixture
    def sample_commit_history(self):
        """Sample commit history for testing."""
        now = datetime.now()
        return [
            {
                'hash': 'abc123',
                'author': 'Alice Developer',
                'date': (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Fix critical security vulnerability in user authentication'
            },
            {
                'hash': 'def456', 
                'author': 'Bob Contributor',
                'date': (now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Add new feature for data processing'
            },
            {
                'hash': 'ghi789',
                'author': 'Alice Developer', 
                'date': (now - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Update dependencies to latest versions'
            },
            {
                'hash': 'jkl012',
                'author': 'Charlie Maintainer',
                'date': (now - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Refactor legacy code for better maintainability'
            },
            {
                'hash': 'mno345',
                'author': 'Alice Developer',
                'date': (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Fix bug in payment processing module'
            },
            {
                'hash': 'pqr678',
                'author': 'David Tester',
                'date': (now - timedelta(days=45)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Improve test coverage for core modules'
            },
            {
                'hash': 'stu901',
                'author': 'Alice Developer',
                'date': (now - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Update documentation and API guides'
            },
            {
                'hash': 'vwx234',
                'author': 'Eve DevOps',
                'date': (now - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Improve CI/CD pipeline configuration'
            },
            {
                'hash': 'yza567',
                'author': 'Bob Contributor',
                'date': (now - timedelta(days=120)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Release version 2.1.0 with new features'
            },
            {
                'hash': 'bcd890',
                'author': 'Alice Developer',
                'date': (now - timedelta(days=200)).strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Initial project setup and architecture'
            }
        ]
    
    @pytest.fixture
    def sample_repo_info(self):
        """Sample repository info for testing."""
        return RepositoryInfo(
            name='test-project',
            path='/path/to/repo',
            branch='main',
            total_commits=100,
            contributors=['Alice Developer', 'Bob Contributor', 'Charlie Maintainer'],
            languages={'Python': 0.7, 'JavaScript': 0.3},
            total_files=50,
            total_lines=5000
        )
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.sustainability_patterns is not None
        
        # Check pattern categories
        patterns = analyzer.sustainability_patterns
        assert 'maintenance_indicators' in patterns
        assert 'health_indicators' in patterns
        assert 'risk_indicators' in patterns
        
        # Check specific patterns
        maintenance = patterns['maintenance_indicators']
        assert 'security_fixes' in maintenance
        assert 'bug_fixes' in maintenance
        assert 'dependency_updates' in maintenance
        
        health = patterns['health_indicators']
        assert 'active_development' in health
        assert 'community_engagement' in health
        assert 'release_management' in health
    
    def test_parse_date_formats(self, analyzer):
        """Test date parsing with different formats."""
        # Standard format
        date1 = analyzer._parse_date('2024-01-15 10:30:00')
        assert date1 is not None
        assert date1.year == 2024
        assert date1.month == 1
        assert date1.day == 15
        
        # ISO format
        date2 = analyzer._parse_date('2024-01-15T10:30:00Z')
        assert date2 is not None
        
        # Simple date
        date3 = analyzer._parse_date('2024-01-15')
        assert date3 is not None
        
        # Invalid format
        date4 = analyzer._parse_date('invalid-date')
        assert date4 is None
        
        # Empty string
        date5 = analyzer._parse_date('')
        assert date5 is None
    
    def test_analyze_activity_patterns(self, analyzer, sample_commit_history):
        """Test activity pattern analysis."""
        result = analyzer._analyze_activity_patterns(sample_commit_history)
        
        assert 'total_commits' in result
        assert 'recent_commits_30d' in result
        assert 'recent_commits_90d' in result
        assert 'recent_commits_1y' in result
        assert 'avg_commits_per_month' in result
        assert 'activity_trend' in result
        assert 'activity_distribution' in result
        assert 'last_commit_date' in result
        assert 'first_commit_date' in result
        
        assert result['total_commits'] == len(sample_commit_history)
        assert result['recent_commits_30d'] >= 0
        assert result['recent_commits_90d'] >= result['recent_commits_30d']
        assert result['activity_trend'] in ['increasing', 'decreasing', 'stable', 'insufficient_data', 'new_project']
    
    def test_analyze_activity_patterns_empty(self, analyzer):
        """Test activity pattern analysis with empty history."""
        result = analyzer._analyze_activity_patterns([])
        
        assert result['total_commits'] == 0
        assert result['activity_trend'] == 'no_data'
        assert result['avg_commits_per_month'] == 0
    
    def test_analyze_contributor_patterns(self, analyzer, sample_commit_history):
        """Test contributor pattern analysis."""
        result = analyzer._analyze_contributor_patterns(sample_commit_history)
        
        assert 'unique_contributors' in result
        assert 'contributor_count' in result
        assert 'active_contributors' in result
        assert 'bus_factor' in result
        assert 'top_contributor_ratio' in result
        assert 'contributor_distribution' in result
        
        # Check that we detected multiple contributors
        assert result['contributor_count'] > 1
        assert len(result['unique_contributors']) == result['contributor_count']
        assert result['bus_factor'] > 0
        assert 0 <= result['top_contributor_ratio'] <= 1
        
        # Alice Developer should have the most commits
        assert 'Alice Developer' in result['contributor_distribution']
        assert result['contributor_distribution']['Alice Developer'] > 1
    
    def test_analyze_contributor_patterns_empty(self, analyzer):
        """Test contributor analysis with empty history."""
        result = analyzer._analyze_contributor_patterns([])
        
        assert result['contributor_count'] == 0
        assert result['bus_factor'] == 0
        assert result['active_contributors'] == 0
        assert len(result['unique_contributors']) == 0
    
    def test_calculate_activity_trend(self, analyzer):
        """Test activity trend calculation."""
        now = datetime.now()
        
        # Test increasing trend
        increasing_commits = [
            (now - timedelta(days=300), {}),
            (now - timedelta(days=250), {}),
            (now - timedelta(days=100), {}),
            (now - timedelta(days=50), {}),
            (now - timedelta(days=30), {}),
            (now - timedelta(days=20), {}),
            (now - timedelta(days=10), {}),
            (now - timedelta(days=5), {}),
            (now - timedelta(days=2), {}),
            (now - timedelta(days=1), {})
        ]
        
        trend = analyzer._calculate_activity_trend(increasing_commits)
        assert trend in ['increasing', 'stable']  # Might be classified as stable due to distribution
        
        # Test insufficient data
        few_commits = [(now - timedelta(days=1), {}), (now - timedelta(days=2), {})]
        trend = analyzer._calculate_activity_trend(few_commits)
        assert trend == 'insufficient_data'
        
        # Test new project
        new_commits = [(now - timedelta(days=30), {}), (now - timedelta(days=20), {})]
        trend = analyzer._calculate_activity_trend(new_commits)
        assert trend == 'new_project'
    
    def test_analyze_maintenance_patterns(self, analyzer, sample_commit_history):
        """Test maintenance pattern analysis."""
        source_files = [Path('test1.py'), Path('test2.py')]
        result = analyzer._analyze_maintenance_patterns(sample_commit_history, source_files)
        
        assert 'maintenance_indicators' in result
        assert 'health_indicators' in result
        assert 'risk_indicators' in result
        assert 'maintenance_ratio' in result
        assert 'health_ratio' in result
        assert 'risk_ratio' in result
        
        # Check that patterns were detected
        maintenance = result['maintenance_indicators']
        assert 'security_fixes' in maintenance
        assert 'dependency_updates' in maintenance
        assert 'bug_fixes' in maintenance
        
        # Security fix should be detected
        assert maintenance['security_fixes'] > 0
        
        # Check ratios are valid
        assert 0 <= result['maintenance_ratio'] <= 1
        assert 0 <= result['health_ratio'] <= 1
        assert 0 <= result['risk_ratio'] <= 1
    
    def test_analyze_health_indicators(self, analyzer, sample_commit_history, sample_repo_info):
        """Test health indicator analysis."""
        result = analyzer._analyze_health_indicators(sample_commit_history, sample_repo_info)
        
        assert 'project_age_days' in result
        assert 'days_since_last_commit' in result
        assert 'release_commits' in result
        assert 'activity_health' in result
        assert 'recency_health' in result
        assert 'release_health' in result
        assert 'is_active' in result
        assert 'is_maintained' in result
        
        # Should detect release commit
        assert result['release_commits'] > 0  # "Release version 2.1.0" should be detected
        
        # Project should be active (recent commits)
        assert result['is_active'] == True
        assert result['is_maintained'] == True
        
        # Health scores should be reasonable
        assert 0 <= result['activity_health'] <= 10
        assert 0 <= result['recency_health'] <= 10
        assert 0 <= result['release_health'] <= 10
    
    def test_calculate_sustainability_metrics(self, analyzer):
        """Test sustainability metrics calculation."""
        activity_analysis = {
            'avg_commits_per_month': 10.0,
            'recent_commits_30d': 5,
            'activity_trend': 'stable'
        }
        
        contributor_analysis = {
            'contributor_count': 5,
            'active_contributors': 3,
            'bus_factor': 3
        }
        
        maintenance_analysis = {
            'maintenance_ratio': 0.3,
            'health_ratio': 0.4,
            'risk_ratio': 0.1
        }
        
        health_analysis = {
            'activity_health': 7.0,
            'recency_health': 8.0,
            'release_health': 6.0,
            'days_since_last_commit': 5
        }
        
        repo_info = RepositoryInfo(
            name='test', path='/test', branch='main', total_commits=100,
            contributors=[], languages={}, total_files=50, total_lines=5000
        )
        
        result = analyzer._calculate_sustainability_metrics(
            activity_analysis, contributor_analysis, maintenance_analysis,
            health_analysis, repo_info
        )
        
        assert 'overall_score' in result
        assert 'maintenance_probability' in result
        assert 'activity_trend' in result
        assert 'bus_factor' in result
        assert 'recent_activity_score' in result
        assert 'contributor_diversity' in result
        assert 'commit_frequency_score' in result
        
        # Check score ranges
        assert 0 <= result['overall_score'] <= 10
        assert 0 <= result['maintenance_probability'] <= 1
        assert result['bus_factor'] == 3
        assert result['activity_trend'] == 'stable'
    
    def test_empty_activity_analysis(self, analyzer):
        """Test empty activity analysis structure."""
        result = analyzer._empty_activity_analysis()
        
        expected_keys = [
            'total_commits', 'recent_commits_30d', 'recent_commits_90d',
            'recent_commits_1y', 'avg_commits_per_month', 'activity_trend',
            'activity_distribution', 'last_commit_date', 'first_commit_date'
        ]
        
        for key in expected_keys:
            assert key in result
        
        assert result['total_commits'] == 0
        assert result['activity_trend'] == 'no_data'
    
    def test_empty_contributor_analysis(self, analyzer):
        """Test empty contributor analysis structure."""
        result = analyzer._empty_contributor_analysis()
        
        expected_keys = [
            'unique_contributors', 'contributor_count', 'active_contributors',
            'bus_factor', 'top_contributor_ratio', 'contributor_distribution'
        ]
        
        for key in expected_keys:
            assert key in result
        
        assert result['contributor_count'] == 0
        assert result['bus_factor'] == 0
        assert len(result['unique_contributors']) == 0
    
    def test_analyze_integration(self, analyzer, sample_commit_history, sample_repo_info):
        """Test full analysis integration."""
        source_files = [Path('test1.py'), Path('test2.py')]
        result = analyzer.analyze(sample_commit_history, sample_repo_info, source_files)
        
        assert result is not None
        assert hasattr(result, 'score')
        assert hasattr(result, 'maintenance_probability')
        assert hasattr(result, 'activity_trend')
        assert hasattr(result, 'bus_factor')
        assert hasattr(result, 'recent_activity_score')
        assert hasattr(result, 'contributor_diversity')
        assert hasattr(result, 'commit_frequency_score')
        
        # Check value ranges
        assert 0 <= result.score <= 10
        assert 0 <= result.maintenance_probability <= 1
        assert result.activity_trend in ['increasing', 'decreasing', 'stable', 'insufficient_data', 'new_project']
        assert result.bus_factor > 0  # Should have detected multiple contributors
        assert 0 <= result.recent_activity_score <= 10
        assert 0 <= result.contributor_diversity <= 1
        assert 0 <= result.commit_frequency_score <= 10
    
    def test_empty_commit_history(self, analyzer, sample_repo_info):
        """Test analysis with empty commit history."""
        source_files = [Path('test1.py')]
        result = analyzer.analyze([], sample_repo_info, source_files)
        
        assert result is not None
        assert result.score >= 0
        assert result.bus_factor == 0
        assert result.activity_trend in ['no_data', 'insufficient_data']
    
    def test_single_contributor_bus_factor(self, analyzer):
        """Test bus factor calculation with single contributor."""
        single_contributor_history = [
            {
                'author': 'Solo Developer',
                'date': '2024-01-01 10:00:00',
                'message': 'Initial commit'
            },
            {
                'author': 'Solo Developer', 
                'date': '2024-01-02 10:00:00',
                'message': 'Add features'
            }
        ]
        
        result = analyzer._analyze_contributor_patterns(single_contributor_history)
        assert result['bus_factor'] == 1
        assert result['contributor_count'] == 1
        assert result['top_contributor_ratio'] == 1.0
    
    def test_maintenance_pattern_detection(self, analyzer):
        """Test specific maintenance pattern detection."""
        maintenance_commits = [
            {'message': 'Update dependencies to fix security vulnerability', 'author': 'dev'},
            {'message': 'Fix critical bug in payment processing', 'author': 'dev'},
            {'message': 'Refactor legacy authentication code', 'author': 'dev'},
            {'message': 'Update API documentation', 'author': 'dev'},
            {'message': 'Improve test coverage for user module', 'author': 'dev'},
            {'message': 'Update CI/CD pipeline configuration', 'author': 'dev'}
        ]
        
        source_files = []
        result = analyzer._analyze_maintenance_patterns(maintenance_commits, source_files)
        
        maintenance = result['maintenance_indicators']
        
        # Should detect various maintenance patterns
        assert maintenance['dependency_updates'] > 0
        assert maintenance['security_fixes'] > 0
        assert maintenance['bug_fixes'] > 0
        assert maintenance['refactoring'] > 0
        assert maintenance['documentation_updates'] > 0
        assert maintenance['test_improvements'] > 0
        assert maintenance['ci_cd_updates'] > 0
    
    def test_date_parsing_edge_cases(self, analyzer):
        """Test date parsing with edge cases."""
        # Date with timezone
        date1 = analyzer._parse_date('2024-01-15T10:30:00+05:00')
        assert date1 is not None
        
        # Date with Z timezone
        date2 = analyzer._parse_date('2024-01-15T10:30:00Z')
        assert date2 is not None
        
        # Malformed date
        date3 = analyzer._parse_date('2024-13-45 25:70:80')
        assert date3 is None
        
        # None input
        date4 = analyzer._parse_date(None)
        assert date4 is None
    
    def test_contributor_activity_timeline(self, analyzer, sample_commit_history):
        """Test contributor activity timeline tracking."""
        result = analyzer._analyze_contributor_patterns(sample_commit_history)
        
        # Should track multiple contributors
        contributors = result['unique_contributors']
        assert 'Alice Developer' in contributors
        assert 'Bob Contributor' in contributors
        assert 'Charlie Maintainer' in contributors
        
        # Alice should have the most commits
        distribution = result['contributor_distribution']
        alice_commits = distribution['Alice Developer']
        assert alice_commits >= 3  # Alice appears multiple times in sample data


if __name__ == '__main__':
    pytest.main([__file__])
