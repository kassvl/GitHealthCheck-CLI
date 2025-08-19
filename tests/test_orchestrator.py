"""Tests for Analysis Orchestrator."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from repo_health_analyzer.core.orchestrator import AnalysisOrchestrator, MetricsCalculator


class TestAnalysisOrchestrator:
    """Test cases for Analysis Orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return AnalysisOrchestrator(verbose=False)
    
    @pytest.fixture
    def verbose_orchestrator(self):
        """Create verbose orchestrator instance for testing."""
        return AnalysisOrchestrator(verbose=True)
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create mock analyzer for testing."""
        analyzer = Mock()
        analyzer.analyze = Mock(return_value={'result': 'test_data'})
        return analyzer
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.verbose == False
        assert orchestrator.analysis_steps == []
        assert orchestrator.api_instance is None
    
    def test_orchestrator_initialization_verbose(self, verbose_orchestrator):
        """Test verbose orchestrator initialization."""
        assert verbose_orchestrator.verbose == True
        assert verbose_orchestrator.analysis_steps == []
    
    def test_register_step_basic(self, orchestrator, mock_analyzer):
        """Test basic step registration."""
        orchestrator.register_step('test_step', mock_analyzer, 'analyze')
        
        assert len(orchestrator.analysis_steps) == 1
        step = orchestrator.analysis_steps[0]
        assert step['name'] == 'test_step'
        assert step['analyzer'] == mock_analyzer
        assert step['method'] == 'analyze'
        assert step['dependencies'] == []
    
    def test_register_step_with_dependencies(self, orchestrator, mock_analyzer):
        """Test step registration with dependencies."""
        dependencies = ['step1', 'step2']
        orchestrator.register_step('test_step', mock_analyzer, 'analyze', dependencies)
        
        step = orchestrator.analysis_steps[0]
        assert step['dependencies'] == dependencies
    
    def test_register_multiple_steps(self, orchestrator):
        """Test registration of multiple steps."""
        analyzer1 = Mock()
        analyzer2 = Mock()
        analyzer3 = Mock()
        
        orchestrator.register_step('step1', analyzer1, 'method1')
        orchestrator.register_step('step2', analyzer2, 'method2', ['step1'])
        orchestrator.register_step('step3', analyzer3, 'method3', ['step1', 'step2'])
        
        assert len(orchestrator.analysis_steps) == 3
        
        # Check dependencies
        steps_by_name = {step['name']: step for step in orchestrator.analysis_steps}
        assert steps_by_name['step1']['dependencies'] == []
        assert steps_by_name['step2']['dependencies'] == ['step1']
        assert steps_by_name['step3']['dependencies'] == ['step1', 'step2']
    
    def test_execute_analysis_simple(self, orchestrator, mock_analyzer):
        """Test simple analysis execution."""
        orchestrator.register_step('test_step', mock_analyzer, 'analyze')
        
        context = {'repo_path': '/fake/repo'}
        results = orchestrator.execute_analysis(context)
        
        assert 'test_step' in results
        assert results['test_step'] == {'result': 'test_data'}
        mock_analyzer.analyze.assert_called_once()
    
    def test_execute_analysis_with_dependencies(self, orchestrator):
        """Test analysis execution with dependencies."""
        # Create mock analyzers
        analyzer1 = Mock()
        analyzer1.method1 = Mock(return_value='result1')
        
        analyzer2 = Mock()
        analyzer2.method2 = Mock(return_value='result2')
        
        # Register steps with dependencies
        orchestrator.register_step('step1', analyzer1, 'method1')
        orchestrator.register_step('step2', analyzer2, 'method2', ['step1'])
        
        context = {}
        results = orchestrator.execute_analysis(context)
        
        # Both steps should complete
        assert 'step1' in results
        assert 'step2' in results
        assert results['step1'] == 'result1'
        assert results['step2'] == 'result2'
        
        # Methods should be called
        analyzer1.method1.assert_called_once()
        analyzer2.method2.assert_called_once()
    
    def test_execute_analysis_circular_dependency(self, orchestrator):
        """Test analysis execution with circular dependencies."""
        analyzer1 = Mock()
        analyzer2 = Mock()
        
        # Create circular dependency
        orchestrator.register_step('step1', analyzer1, 'method1', ['step2'])
        orchestrator.register_step('step2', analyzer2, 'method2', ['step1'])
        
        context = {}
        
        # Should raise RuntimeError for circular dependency
        with pytest.raises(RuntimeError, match="Cannot resolve dependencies"):
            orchestrator.execute_analysis(context)
    
    def test_execute_step_method_with_parameters(self, orchestrator):
        """Test step method execution with parameter mapping."""
        # Create analyzer with method that expects specific parameters
        analyzer = Mock()
        
        def mock_method(source_files, repo_path):
            return {'files': len(source_files), 'path': str(repo_path)}
        
        analyzer.analyze = mock_method
        
        orchestrator.register_step('test_step', analyzer, 'analyze')
        
        context = {
            'repo_path': '/fake/repo',
            'source_files': ['/fake/file1.py', '/fake/file2.py']
        }
        
        results = orchestrator.execute_analysis(context)
        
        assert 'test_step' in results
        assert results['test_step']['files'] == 2
        assert results['test_step']['path'] == '/fake/repo'
    
    def test_execute_step_method_no_parameters(self, orchestrator, mock_analyzer):
        """Test step method execution with no parameters."""
        # Method that takes no parameters
        mock_analyzer.no_param_method = Mock(return_value='no_params_result')
        
        orchestrator.register_step('test_step', mock_analyzer, 'no_param_method')
        
        context = {'some_data': 'value'}
        results = orchestrator.execute_analysis(context)
        
        assert results['test_step'] == 'no_params_result'
        mock_analyzer.no_param_method.assert_called_once_with()
    
    def test_execute_step_method_with_results_dependency(self, orchestrator):
        """Test step method execution using results from previous steps."""
        # First analyzer
        analyzer1 = Mock()
        analyzer1.get_data = Mock(return_value=['file1.py', 'file2.py'])
        
        # Second analyzer that depends on first
        analyzer2 = Mock()
        
        def mock_analyze(*args, **kwargs):
            source_files = kwargs.get('source_files', args[0] if args else [])
            if hasattr(source_files, '__len__'):
                return {'analyzed_files': len(source_files)}
            return {'analyzed_files': 0}
        
        analyzer2.analyze = mock_analyze
        
        # Register steps
        orchestrator.register_step('get_files', analyzer1, 'get_data')
        orchestrator.register_step('analyze_files', analyzer2, 'analyze', ['get_files'])
        
        context = {}
        results = orchestrator.execute_analysis(context)
        
        assert 'get_files' in results
        assert 'analyze_files' in results
        assert results['get_files'] == ['file1.py', 'file2.py']
        assert results['analyze_files']['analyzed_files'] == 2
    
    def test_progress_tracking_with_api(self, orchestrator, mock_analyzer):
        """Test progress tracking with API instance."""
        # Mock API instance
        api_instance = Mock()
        api_instance.current_step = None
        api_instance.current_progress = 0
        orchestrator.api_instance = api_instance
        
        orchestrator.register_step('code_quality', mock_analyzer, 'analyze')
        
        context = {}
        orchestrator.execute_analysis(context)
        
        # Check that progress was updated
        assert api_instance.current_step == 'Evaluating code quality...'
        assert api_instance.current_progress == 0.0  # 0% when starting first step


class TestMetricsCalculator:
    """Test cases for Metrics Calculator."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Sample metrics for testing."""
        return {
            'code_quality': Mock(overall_score=8.5),
            'architecture': Mock(score=7.2),
            'code_smells': Mock(severity_score=6.8),
            'tests': Mock(coverage_score=7.5),
            'documentation': Mock(score=6.0),
            'sustainability': Mock(score=8.0)
        }
    
    def test_calculate_overall_metrics(self, sample_metrics):
        """Test overall metrics calculation."""
        result = MetricsCalculator.calculate_overall_metrics(
            sample_metrics['code_quality'],
            sample_metrics['architecture'],
            sample_metrics['code_smells'],
            sample_metrics['tests'],
            sample_metrics['documentation'],
            sample_metrics['sustainability']
        )
        
        assert result is not None
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'code_quality')
        assert hasattr(result, 'architecture')
        assert hasattr(result, 'code_smells')
        assert hasattr(result, 'tests')
        assert hasattr(result, 'documentation')
        assert hasattr(result, 'sustainability')
        
        # Check that overall score is reasonable
        assert 0 <= result.overall_score <= 10
        
        # Check that individual metrics are preserved
        assert result.code_quality == sample_metrics['code_quality']
        assert result.architecture == sample_metrics['architecture']
        assert result.code_smells == sample_metrics['code_smells']
        assert result.tests == sample_metrics['tests']
        assert result.documentation == sample_metrics['documentation']
        assert result.sustainability == sample_metrics['sustainability']
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Create mock overall metrics with proper numeric attributes
        overall_metrics = Mock()
        overall_metrics.overall_score = 6.5
        
        # Create mock sub-metrics with proper numeric attributes
        code_quality_mock = Mock()
        code_quality_mock.overall_score = 5.0
        code_quality_mock.comment_density = 0.15
        code_quality_mock.function_length_avg = 25.0
        code_quality_mock.naming_consistency = 0.8
        overall_metrics.code_quality = code_quality_mock
        
        architecture_mock = Mock()
        architecture_mock.score = 7.0
        architecture_mock.circular_dependencies = 2
        overall_metrics.architecture = architecture_mock
        
        code_smells_mock = Mock()
        code_smells_mock.severity_score = 4.0
        code_smells_mock.total_count = 15
        overall_metrics.code_smells = code_smells_mock
        
        tests_mock = Mock()
        tests_mock.coverage_score = 3.0
        tests_mock.test_files_count = 2
        overall_metrics.tests = tests_mock
        
        documentation_mock = Mock()
        documentation_mock.score = 4.5
        documentation_mock.docstring_coverage = 0.3
        overall_metrics.documentation = documentation_mock
        
        sustainability_mock = Mock()
        sustainability_mock.score = 8.0
        sustainability_mock.bus_factor = 1
        overall_metrics.sustainability = sustainability_mock
        
        recommendations = MetricsCalculator.generate_recommendations(overall_metrics)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should generate recommendations for low scores
        recommendation_categories = [r.category for r in recommendations]
        assert 'code_quality' in recommendation_categories  # Score 5.0 < 6.0
        assert 'code_smells' in recommendation_categories   # Score 4.0 < 6.0
        assert 'tests' in recommendation_categories         # Score 3.0 < 6.0
        assert 'documentation' in recommendation_categories # Score 4.5 < 6.0
        
        # Check recommendation properties
        for rec in recommendations:
            assert hasattr(rec, 'category')
            assert hasattr(rec, 'priority')
            assert hasattr(rec, 'title')
            assert hasattr(rec, 'description')
            assert rec.priority in ['critical', 'high', 'medium', 'low']
    
    def test_generate_recommendations_high_scores(self):
        """Test recommendation generation with high scores."""
        # Create mock metrics with high scores and proper numeric attributes
        overall_metrics = Mock()
        overall_metrics.overall_score = 9.0
        
        code_quality_mock = Mock()
        code_quality_mock.overall_score = 9.5
        code_quality_mock.comment_density = 0.25
        code_quality_mock.function_length_avg = 15.0
        code_quality_mock.naming_consistency = 0.95
        overall_metrics.code_quality = code_quality_mock
        
        architecture_mock = Mock()
        architecture_mock.score = 9.0
        architecture_mock.circular_dependencies = 0
        overall_metrics.architecture = architecture_mock
        
        code_smells_mock = Mock()
        code_smells_mock.severity_score = 9.2
        code_smells_mock.total_count = 2
        overall_metrics.code_smells = code_smells_mock
        
        tests_mock = Mock()
        tests_mock.coverage_score = 8.5
        tests_mock.test_files_count = 25
        overall_metrics.tests = tests_mock
        
        documentation_mock = Mock()
        documentation_mock.score = 8.0
        documentation_mock.docstring_coverage = 0.9
        overall_metrics.documentation = documentation_mock
        
        sustainability_mock = Mock()
        sustainability_mock.score = 9.0
        sustainability_mock.bus_factor = 5
        overall_metrics.sustainability = sustainability_mock
        
        recommendations = MetricsCalculator.generate_recommendations(overall_metrics)
        
        # Should generate fewer or no recommendations for high scores
        assert isinstance(recommendations, list)
        # High scores might still generate some optimization recommendations
        if recommendations:
            for rec in recommendations:
                assert rec.priority in ['low', 'medium']  # Should not be critical/high priority
    
    def test_recommendation_priority_assignment(self):
        """Test that recommendations get appropriate priority levels."""
        # Test critical priority with proper numeric attributes
        overall_metrics = Mock()
        overall_metrics.overall_score = 2.0  # Very low
        
        code_quality_mock = Mock()
        code_quality_mock.overall_score = 1.5
        code_quality_mock.comment_density = 0.05
        code_quality_mock.function_length_avg = 80.0
        code_quality_mock.naming_consistency = 0.3
        overall_metrics.code_quality = code_quality_mock
        
        architecture_mock = Mock()
        architecture_mock.score = 2.0
        architecture_mock.circular_dependencies = 5
        overall_metrics.architecture = architecture_mock
        
        code_smells_mock = Mock()
        code_smells_mock.severity_score = 1.0
        code_smells_mock.total_count = 50
        overall_metrics.code_smells = code_smells_mock
        
        tests_mock = Mock()
        tests_mock.coverage_score = 0.5
        tests_mock.test_files_count = 0
        overall_metrics.tests = tests_mock
        
        documentation_mock = Mock()
        documentation_mock.score = 1.0
        documentation_mock.docstring_coverage = 0.1
        overall_metrics.documentation = documentation_mock
        
        sustainability_mock = Mock()
        sustainability_mock.score = 2.0
        sustainability_mock.bus_factor = 1
        overall_metrics.sustainability = sustainability_mock
        
        recommendations = MetricsCalculator.generate_recommendations(overall_metrics)
        
        # Should have critical/high priority recommendations
        priorities = [r.priority for r in recommendations]
        assert 'critical' in priorities or 'high' in priorities
    
    def test_empty_metrics_handling(self):
        """Test handling of None or empty metrics."""
        # Test with None metrics
        result = MetricsCalculator.calculate_overall_metrics(None, None, None, None, None, None)
        assert result is not None
        assert result.overall_score >= 0
        
        # Test recommendations with None metrics
        recommendations = MetricsCalculator.generate_recommendations(None)
        assert isinstance(recommendations, list)


class TestOrchestrationWorkflow:
    """Test cases for orchestration workflow."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create basic orchestrator instance for testing."""
        return AnalysisOrchestrator(verbose=False)
    
    @pytest.fixture
    def verbose_orchestrator(self):
        """Create verbose orchestrator instance for testing."""
        return AnalysisOrchestrator(verbose=True)
    
    @pytest.fixture
    def mock_analyzer(self):
        """Create mock analyzer for testing."""
        analyzer = Mock()
        analyzer.analyze = Mock(return_value={'result': 'test_data'})
        return analyzer
    
    @pytest.fixture
    def orchestrator_with_steps(self):
        """Create orchestrator with registered steps."""
        orchestrator = AnalysisOrchestrator(verbose=False)
        
        # Create mock analyzers
        git_parser = Mock()
        git_parser.get_repository_info = Mock(return_value={'repo': 'info'})
        git_parser.get_source_files = Mock(return_value=['file1.py', 'file2.py'])
        git_parser.get_commit_history = Mock(return_value=[{'commit': 'data'}])
        
        code_analyzer = Mock()
        code_analyzer.analyze = Mock(return_value={'quality': 'metrics'})
        
        # Register steps
        orchestrator.register_step('git_parsing', git_parser, 'get_repository_info')
        orchestrator.register_step('source_files', git_parser, 'get_source_files')
        orchestrator.register_step('commit_history', git_parser, 'get_commit_history')
        orchestrator.register_step('code_quality', code_analyzer, 'analyze', ['source_files'])
        
        return orchestrator, git_parser, code_analyzer
    
    def test_workflow_execution_order(self, orchestrator_with_steps):
        """Test that workflow executes steps in correct dependency order."""
        orchestrator, git_parser, code_analyzer = orchestrator_with_steps
        
        context = {'repo_path': '/fake/repo'}
        results = orchestrator.execute_analysis(context)
        
        # All steps should complete
        assert 'git_parsing' in results
        assert 'source_files' in results
        assert 'commit_history' in results
        assert 'code_quality' in results
        
        # Check that methods were called
        git_parser.get_repository_info.assert_called_once()
        git_parser.get_source_files.assert_called_once()
        git_parser.get_commit_history.assert_called_once()
        code_analyzer.analyze.assert_called_once()
        
        # Check results
        assert results['git_parsing'] == {'repo': 'info'}
        assert results['source_files'] == ['file1.py', 'file2.py']
        assert results['commit_history'] == [{'commit': 'data'}]
        assert results['code_quality'] == {'quality': 'metrics'}
    
    def test_workflow_dependency_resolution(self):
        """Test complex dependency resolution."""
        orchestrator = AnalysisOrchestrator(verbose=False)
        
        # Create analyzers
        analyzers = {f'analyzer_{i}': Mock() for i in range(5)}
        
        # Setup methods
        for i, analyzer in enumerate(analyzers.values()):
            setattr(analyzer, 'analyze', Mock(return_value=f'result_{i}'))
        
        # Register steps with complex dependencies
        orchestrator.register_step('step_a', analyzers['analyzer_0'], 'analyze')
        orchestrator.register_step('step_b', analyzers['analyzer_1'], 'analyze', ['step_a'])
        orchestrator.register_step('step_c', analyzers['analyzer_2'], 'analyze', ['step_a'])
        orchestrator.register_step('step_d', analyzers['analyzer_3'], 'analyze', ['step_b', 'step_c'])
        orchestrator.register_step('step_e', analyzers['analyzer_4'], 'analyze', ['step_d'])
        
        context = {}
        results = orchestrator.execute_analysis(context)
        
        # All steps should complete
        assert len(results) == 5
        assert all(f'step_{letter}' in results for letter in 'abcde')
    
    def test_workflow_with_missing_dependency(self):
        """Test workflow with missing dependency."""
        orchestrator = AnalysisOrchestrator(verbose=False)
        
        analyzer = Mock()
        analyzer.analyze = Mock(return_value='result')
        
        # Register step with non-existent dependency
        orchestrator.register_step('dependent_step', analyzer, 'analyze', ['non_existent_step'])
        
        context = {}
        
        # Should raise RuntimeError for missing dependency
        with pytest.raises(RuntimeError, match="Cannot resolve dependencies"):
            orchestrator.execute_analysis(context)
    
    def test_parameter_mapping_edge_cases(self, orchestrator):
        """Test parameter mapping edge cases."""
        # Analyzer with method that has unusual parameter names
        analyzer = Mock()
        
        def custom_method(custom_param, another_param=None):
            return {'custom': custom_param, 'another': another_param}
        
        analyzer.custom_method = custom_method
        
        orchestrator.register_step('custom_step', analyzer, 'custom_method')
        
        context = {
            'custom_param': 'custom_value',
            'another_param': 'another_value'
        }
        
        results = orchestrator.execute_analysis(context)
        
        assert 'custom_step' in results
        assert results['custom_step']['custom'] == 'custom_value'
        assert results['custom_step']['another'] == 'another_value'
    
    def test_source_files_limiting(self):
        """Test source files limiting for large repositories."""
        orchestrator = AnalysisOrchestrator(verbose=True)
        
        analyzer = Mock()
        
        def analyze_with_files(source_files):
            return {'file_count': len(source_files)}
        
        analyzer.analyze = analyze_with_files
        
        orchestrator.register_step('test_step', analyzer, 'analyze')
        
        # Create context with many files
        large_file_list = [f'file_{i}.py' for i in range(1500)]  # More than 1000 limit
        context = {'source_files': large_file_list}
        
        results = orchestrator.execute_analysis(context)
        
        # Should limit to 1000 files
        assert results['test_step']['file_count'] == 1000
    
    def test_verbose_output(self, verbose_orchestrator, mock_analyzer):
        """Test verbose output during execution."""
        verbose_orchestrator.register_step('test_step', mock_analyzer, 'analyze')
        
        context = {}
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            verbose_orchestrator.execute_analysis(context)
            
            # Should have printed debug information
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any('Executing: test_step' in call for call in print_calls)


if __name__ == '__main__':
    pytest.main([__file__])
