"""Tests for Code Quality Analyzer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from repo_health_analyzer.core.analyzers.code_quality_analyzer import CodeQualityAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestCodeQualityAnalyzer:
    """Test cases for Code Quality Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return CodeQualityAnalyzer(config)
    
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return '''
"""Module docstring."""

import os
import sys

class TestClass:
    """Test class docstring."""
    
    def __init__(self, name: str):
        self.name = name
    
    def simple_method(self) -> str:
        """Simple method with type hints."""
        return f"Hello {self.name}"
    
    def complex_method(self, a: int, b: int, c: int) -> int:
        """Complex method for testing."""
        if a > 10:
            if b > 5:
                if c > 2:
                    return a + b + c
                else:
                    return a + b
            else:
                return a
        else:
            return 0

def test_function():
    """Test function."""
    # This is a comment
    x = 42  # Magic number
    assert x == 42
    
# TODO: Add more tests
'''
    
    @pytest.fixture
    def sample_javascript_code(self):
        """Sample JavaScript code for testing."""
        return '''
/**
 * JavaScript test module
 */

const express = require('express');

class UserService {
    constructor(database) {
        this.db = database;
    }
    
    async getUser(id) {
        if (id > 0) {
            const user = await this.db.findUser(id);
            return user;
        }
        return null;
    }
    
    validateUser(user) {
        // Complex validation
        if (user && user.name && user.email) {
            if (user.name.length > 2) {
                if (user.email.includes('@')) {
                    return true;
                }
            }
        }
        return false;
    }
}

// TODO: Add error handling
module.exports = UserService;
'''
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.language_patterns is not None
        assert analyzer.code_smells is not None
        assert 'python' in analyzer.language_patterns
        assert 'javascript' in analyzer.language_patterns
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language('.py') == 'python'
        assert analyzer._detect_language('.js') == 'javascript'
        assert analyzer._detect_language('.java') == 'java'
        assert analyzer._detect_language('.unknown') == 'generic'
    
    def test_calculate_complexity_regex_python(self, analyzer, sample_python_code):
        """Test complexity calculation for Python code."""
        patterns = analyzer.language_patterns['python']
        complexity_scores = analyzer._calculate_complexity_regex(sample_python_code, patterns)
        
        assert len(complexity_scores) > 0
        assert all(score >= 1 for score in complexity_scores)
        assert max(complexity_scores) >= 3  # complex_method should have higher complexity
    
    def test_calculate_function_lengths(self, analyzer, sample_python_code):
        """Test function length calculation."""
        patterns = analyzer.language_patterns['python']
        function_lengths = analyzer._calculate_function_lengths(sample_python_code, patterns)
        
        assert len(function_lengths) > 0
        assert all(length > 0 for length in function_lengths)
    
    def test_calculate_comment_ratio_advanced(self, analyzer, sample_python_code):
        """Test comment ratio calculation."""
        patterns = analyzer.language_patterns['python']
        comment_ratio = analyzer._calculate_comment_ratio_advanced(sample_python_code, patterns)
        
        assert 0 <= comment_ratio <= 1
        assert comment_ratio > 0  # Sample code has comments
    
    def test_calculate_naming_consistency(self, analyzer, sample_python_code):
        """Test naming consistency calculation."""
        patterns = analyzer.language_patterns['python']
        naming_score = analyzer._calculate_naming_consistency(sample_python_code, patterns)
        
        assert 0 <= naming_score <= 1
        assert naming_score > 0.5  # Sample code follows conventions
    
    def test_detect_code_duplication(self, analyzer):
        """Test code duplication detection."""
        duplicate_code = '''
def method1():
    x = 1
    y = 2
    z = x + y
    return z

def method2():
    x = 1
    y = 2
    z = x + y
    return z
'''
        duplication_score = analyzer._detect_code_duplication(duplicate_code)
        assert duplication_score > 0  # Should detect duplication
    
    def test_count_code_smells(self, analyzer, sample_python_code):
        """Test code smell counting."""
        smell_count = analyzer._count_code_smells(sample_python_code)
        assert smell_count >= 0
    
    def test_calculate_type_hint_coverage_python(self, analyzer, sample_python_code):
        """Test type hint coverage calculation for Python."""
        coverage = analyzer._calculate_type_hint_coverage(sample_python_code, 'python')
        assert 0 <= coverage <= 1
        assert coverage > 0  # Sample code has type hints
    
    def test_calculate_type_hint_coverage_non_python(self, analyzer):
        """Test type hint coverage for non-Python languages."""
        coverage = analyzer._calculate_type_hint_coverage('', 'javascript')
        assert coverage == 0.0
    
    def test_calculate_error_handling_density(self, analyzer):
        """Test error handling density calculation."""
        code_with_error_handling = '''
def risky_function():
    try:
        result = dangerous_operation()
        return result
    except ValueError as e:
        raise CustomError(f"Error: {e}")
    finally:
        cleanup()
'''
        patterns = analyzer.language_patterns['python']
        density = analyzer._calculate_error_handling_density(code_with_error_handling, patterns)
        assert density > 0
    
    def test_calculate_line_length_violations(self, analyzer):
        """Test line length violation calculation."""
        long_lines = [
            "short line",
            "this is a very long line that exceeds the maximum allowed length for good coding practices and readability standards",
            "another short line"
        ]
        patterns = {'long_lines': 50}
        violations = analyzer._calculate_line_length_violations(long_lines, patterns)
        assert violations > 0
    
    def test_calculate_indentation_consistency(self, analyzer):
        """Test indentation consistency calculation."""
        consistent_code = [
            "def function():",
            "    if True:",
            "        return 42",
            "    else:",
            "        return 0"
        ]
        consistency = analyzer._calculate_indentation_consistency(consistent_code)
        assert consistency >= 0.7  # Should be consistent
        
        inconsistent_code = [
            "def function():",
            "  if True:",  # 2 spaces
            "      return 42",  # 6 spaces
            "   else:",  # 3 spaces
            "        return 0"  # 8 spaces
        ]
        consistency = analyzer._calculate_indentation_consistency(inconsistent_code)
        assert consistency < 0.7  # Should be inconsistent
    
    def test_count_todos_and_fixmes(self, analyzer, sample_python_code):
        """Test TODO and FIXME counting."""
        count = analyzer._count_todos_and_fixmes(sample_python_code)
        assert count > 0  # Sample code has TODO
    
    @patch('builtins.open', mock_open(read_data='def test(): pass'))
    def test_analyze_file_comprehensive(self, analyzer):
        """Test comprehensive file analysis."""
        test_file = Path('test.py')
        result = analyzer._analyze_file_comprehensive(test_file)
        
        assert result is not None
        assert 'language' in result
        assert 'complexity' in result
        assert 'function_lengths' in result
        assert result['language'] == 'python'
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_file_comprehensive_error(self, mock_open, analyzer):
        """Test file analysis with IO error."""
        test_file = Path('nonexistent.py')
        result = analyzer._analyze_file_comprehensive(test_file)
        assert result == {}
    
    def test_calculate_comprehensive_scores(self, analyzer):
        """Test comprehensive score calculation."""
        all_metrics = {
            'complexity': [1, 2, 3, 4, 5],
            'function_lengths': [10, 20, 30],
            'comment_ratios': [0.1, 0.2, 0.15],
            'naming_scores': [0.8, 0.9, 0.85],
            'duplication_scores': [0.05, 0.02, 0.03],
            'smell_counts': [2, 1, 3],
            'type_hint_ratios': [0.7, 0.8, 0.6],
            'error_handling_ratios': [0.3, 0.4, 0.2],
            'line_violations': [0.05, 0.02, 0.08]
        }
        
        scores = analyzer._calculate_comprehensive_scores(all_metrics, 1000, 50)
        
        assert 'overall_score' in scores
        assert 'avg_complexity' in scores
        assert 0 <= scores['overall_score'] <= 10
        assert scores['avg_complexity'] == 3.0  # Average of [1,2,3,4,5]
    
    @patch('builtins.open', mock_open())
    def test_analyze_integration(self, analyzer, sample_python_code):
        """Test full analysis integration."""
        with patch('builtins.open', mock_open(read_data=sample_python_code)):
            test_files = [Path('test1.py'), Path('test2.py')]
            result = analyzer.analyze(test_files)
            
            assert result is not None
            assert hasattr(result, 'overall_score')
            assert hasattr(result, 'cyclomatic_complexity')
            assert hasattr(result, 'comment_density')
            assert 0 <= result.overall_score <= 10
    
    def test_empty_file_list(self, analyzer):
        """Test analysis with empty file list."""
        result = analyzer.analyze([])
        assert result is not None
        assert result.overall_score >= 0
    
    def test_javascript_analysis(self, analyzer, sample_javascript_code):
        """Test JavaScript code analysis."""
        patterns = analyzer.language_patterns['javascript']
        complexity_scores = analyzer._calculate_complexity_regex(sample_javascript_code, patterns)
        
        assert len(complexity_scores) >= 0
        
        comment_ratio = analyzer._calculate_comment_ratio_advanced(sample_javascript_code, patterns)
        assert comment_ratio >= 0
    
    def test_generate_quality_insights(self, analyzer):
        """Test quality insights generation."""
        file_details = [
            {'complexity': [1, 2, 20], 'file_path': 'test1.py'},
            {'complexity': [3, 4], 'file_path': 'test2.py'}
        ]
        metrics_summary = {
            'avg_complexity': 6.0,
            'avg_comment_density': 0.05,
            'avg_duplication': 0.15,
            'avg_naming_score': 0.7
        }
        
        insights = analyzer._generate_quality_insights(file_details, metrics_summary)
        
        assert 'complexity_hotspots' in insights
        assert 'recommendations' in insights
        assert len(insights['complexity_hotspots']) > 0
        assert len(insights['recommendations']) > 0


if __name__ == '__main__':
    pytest.main([__file__])
