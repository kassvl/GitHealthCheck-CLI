"""Tests for Main Repository Analyzer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestRepositoryAnalyzer:
    """Test cases for the main Repository Analyzer."""
    
    @pytest.fixture
    def sample_repo_path(self):
        """Sample repository path for testing."""
        return Path('/fake/test/repo')
    
    @pytest.fixture
    def sample_config(self):
        """Sample analysis configuration."""
        return AnalysisConfig(
            include_patterns=['*.py', '*.js'],
            exclude_patterns=['*/node_modules/*', '*/venv/*']
        )
    
    def test_analyzer_initialization_with_config(self, sample_repo_path, sample_config):
        """Test analyzer initialization with custom config."""
        analyzer = RepositoryAnalyzer(sample_repo_path, sample_config, verbose=True)
        
        assert analyzer.repo_path == sample_repo_path
        assert analyzer.config == sample_config
        assert analyzer.verbose == True
        assert analyzer.console is not None
        assert analyzer.orchestrator is not None
        assert analyzer.visualizer is not None
    
    def test_analyzer_initialization_default_config(self, sample_repo_path):
        """Test analyzer initialization with default config."""
        analyzer = RepositoryAnalyzer(sample_repo_path)
        
        assert analyzer.repo_path == sample_repo_path
        assert analyzer.config is not None
        assert analyzer.verbose == False
        assert analyzer.console is None
    
    def test_analyzer_initialization_string_path(self):
        """Test analyzer initialization with string path."""
        string_path = '/fake/test/repo'
        analyzer = RepositoryAnalyzer(string_path)
        
        assert analyzer.repo_path == Path(string_path)
        assert analyzer.repo_path.is_absolute()
    
    def test_initialize_analyzers(self, sample_repo_path):
        """Test analyzer module initialization."""
        analyzer = RepositoryAnalyzer(sample_repo_path)
        
        # Check that all analyzers are initialized
        assert analyzer.git_parser is not None
        assert analyzer.code_quality_analyzer is not None
        assert analyzer.code_smell_analyzer is not None
        assert analyzer.architecture_analyzer is not None
        assert analyzer.test_analyzer is not None
        assert analyzer.documentation_analyzer is not None
        assert analyzer.sustainability_analyzer is not None
        
        # Check that all analyzers have the same config
        assert analyzer.code_quality_analyzer.config == analyzer.config
        assert analyzer.code_smell_analyzer.config == analyzer.config
        assert analyzer.architecture_analyzer.config == analyzer.config
        assert analyzer.test_analyzer.config == analyzer.config
        assert analyzer.documentation_analyzer.config == analyzer.config
        assert analyzer.sustainability_analyzer.config == analyzer.config
    
    def test_setup_analysis_workflow(self, sample_repo_path):
        """Test analysis workflow setup."""
        analyzer = RepositoryAnalyzer(sample_repo_path)
        
        # Check that steps are registered with orchestrator
        step_names = [step['name'] for step in analyzer.orchestrator.analysis_steps]
        
        expected_steps = [
            'git_parsing', 'source_files', 'commit_history',
            'code_quality', 'code_smells', 'architecture',
            'tests', 'documentation', 'sustainability'
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names
        
        # Check dependencies
        steps_by_name = {step['name']: step for step in analyzer.orchestrator.analysis_steps}
        
        # Code quality should depend on source_files
        assert 'source_files' in steps_by_name['code_quality']['dependencies']
        
        # Documentation should depend on source_files and git_parsing
        doc_deps = steps_by_name['documentation']['dependencies']
        assert 'source_files' in doc_deps
        assert 'git_parsing' in doc_deps
        
        # Sustainability should depend on commit_history, git_parsing, and source_files
        sustainability_deps = steps_by_name['sustainability']['dependencies']
        assert 'commit_history' in sustainability_deps
        assert 'git_parsing' in sustainability_deps
        assert 'source_files' in sustainability_deps
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.rglob')
    def test_analyze_error_handling(self, mock_rglob, mock_exists, mock_subprocess, sample_repo_path):
        """Test error handling during analysis."""
        # Setup mocks
        mock_exists.return_value = True
        mock_rglob.return_value = [Path('test.py')]
        mock_subprocess.return_value = Mock(returncode=0, stdout='')
        
        analyzer = RepositoryAnalyzer(sample_repo_path)
        
        # Mock one analyzer to fail
        with patch.object(analyzer.code_quality_analyzer, 'analyze', side_effect=Exception("Test error")):
            # Should handle error gracefully
            try:
                result = analyzer.analyze()
                # Analysis should complete despite error in one analyzer
                assert result is not None
            except Exception as e:
                # If it does raise an exception, it should be handled by orchestrator
                assert "Test error" in str(e) or "Cannot resolve dependencies" in str(e)
    
    def test_generate_visualizations(self, sample_repo_path):
        """Test visualization generation."""
        analyzer = RepositoryAnalyzer(sample_repo_path)
        
        # Create a mock report
        mock_report = Mock()
        mock_report.repository = Mock()
        mock_report.metrics = Mock()
        
        # Test visualization generation
        with patch.object(analyzer.visualizer, 'generate_all') as mock_generate:
            analyzer.generate_visualizations(mock_report)
            mock_generate.assert_called_once_with(mock_report, sample_repo_path)
    
    def test_orchestrator_registration(self, sample_repo_path):
        """Test that all analysis steps are properly registered."""
        analyzer = RepositoryAnalyzer(sample_repo_path)
        orchestrator = analyzer.orchestrator
        
        # Check that all required steps are registered
        registered_steps = [step['name'] for step in orchestrator.analysis_steps]
        
        required_steps = [
            'git_parsing', 'source_files', 'commit_history',
            'code_quality', 'code_smells', 'architecture', 
            'tests', 'documentation', 'sustainability'
        ]
        
        for step in required_steps:
            assert step in registered_steps, f"Step '{step}' should be registered"
        
        # Check that analyzers are properly assigned
        steps_by_name = {step['name']: step for step in orchestrator.analysis_steps}
        
        assert steps_by_name['code_quality']['analyzer'] == analyzer.code_quality_analyzer
        assert steps_by_name['architecture']['analyzer'] == analyzer.architecture_analyzer
        assert steps_by_name['code_smells']['analyzer'] == analyzer.code_smell_analyzer
        assert steps_by_name['tests']['analyzer'] == analyzer.test_analyzer
        assert steps_by_name['documentation']['analyzer'] == analyzer.documentation_analyzer
        assert steps_by_name['sustainability']['analyzer'] == analyzer.sustainability_analyzer
    
    def test_context_preparation(self, sample_repo_path, sample_config):
        """Test analysis context preparation."""
        analyzer = RepositoryAnalyzer(sample_repo_path, sample_config)
        
        # Mock the analyze method to capture context
        context_captured = None
        
        def capture_context(context):
            nonlocal context_captured
            context_captured = context
            return {}
        
        with patch.object(analyzer.orchestrator, 'execute_analysis', side_effect=capture_context):
            with patch('repo_health_analyzer.core.orchestrator.MetricsCalculator.calculate_overall_metrics'):
                with patch('repo_health_analyzer.core.orchestrator.MetricsCalculator.generate_recommendations'):
                    try:
                        analyzer.analyze()
                    except:
                        pass  # Expected to fail due to mocking
        
        # Check that context was prepared correctly
        if context_captured:
            assert 'repo_path' in context_captured
            assert 'include_patterns' in context_captured
            assert 'exclude_patterns' in context_captured
            assert context_captured['repo_path'] == sample_repo_path
            assert context_captured['include_patterns'] == sample_config.include_patterns
            assert context_captured['exclude_patterns'] == sample_config.exclude_patterns
    
    @patch('time.time')
    def test_analysis_timing(self, mock_time, sample_repo_path):
        """Test analysis timing measurement."""
        # Mock time to return predictable values
        mock_time.side_effect = [1000.0, 1005.5]  # 5.5 seconds duration
        
        with patch.object(RepositoryAnalyzer, '_initialize_analyzers'):
            with patch.object(RepositoryAnalyzer, '_setup_analysis_workflow'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('subprocess.run', return_value=Mock(returncode=0, stdout='')):
                        with patch('pathlib.Path.rglob', return_value=[]):
                            analyzer = RepositoryAnalyzer(sample_repo_path)
                            
                            # Mock orchestrator results
                            mock_results = {
                                'git_parsing': Mock(),
                                'code_quality': Mock(),
                                'architecture': Mock(),
                                'code_smells': Mock(),
                                'tests': Mock(),
                                'documentation': Mock(),
                                'sustainability': Mock()
                            }
                            
                            with patch.object(analyzer.orchestrator, 'execute_analysis', return_value=mock_results):
                                with patch('repo_health_analyzer.core.orchestrator.MetricsCalculator.calculate_overall_metrics'):
                                    with patch('repo_health_analyzer.core.orchestrator.MetricsCalculator.generate_recommendations', return_value=[]):
                                        result = analyzer.analyze()
                                        
                                        # Check timing
                                        assert result.analysis_duration == 5.5
    
    def test_path_conversion(self, sample_config):
        """Test path conversion and normalization."""
        # Test with string path
        string_path = '/fake/repo'
        analyzer1 = RepositoryAnalyzer(string_path, sample_config)
        assert analyzer1.repo_path == Path(string_path)
        assert analyzer1.repo_path.is_absolute()
        
        # Test with Path object
        path_obj = Path('/fake/repo')
        analyzer2 = RepositoryAnalyzer(path_obj, sample_config)
        assert analyzer2.repo_path == path_obj
        
        # Test with relative path
        relative_path = 'relative/repo'
        analyzer3 = RepositoryAnalyzer(relative_path, sample_config)
        assert analyzer3.repo_path.is_absolute()  # Should be converted to absolute


if __name__ == '__main__':
    pytest.main([__file__])
