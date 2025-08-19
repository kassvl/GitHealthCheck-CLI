"""Tests for Documentation Analyzer."""

import pytest
import re
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from repo_health_analyzer.core.analyzers.documentation_analyzer import DocumentationAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestDocumentationAnalyzer:
    """Test cases for Documentation Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return DocumentationAnalyzer(config)
    
    @pytest.fixture
    def sample_readme_content(self):
        """Sample README content for testing."""
        return '''
# My Project

A comprehensive project that does amazing things.

## Installation

```bash
pip install my-project
```

## Usage

Here's how to use the project:

```python
from my_project import MyClass

obj = MyClass()
result = obj.process()
```

## API Reference

### MyClass

The main class that handles processing.

#### Methods

- `process()`: Processes the data
- `validate()`: Validates input data

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct.

## License

This project is licensed under the MIT License.

## Links

- [Documentation](https://docs.example.com)
- [GitHub](https://github.com/user/project)
'''
    
    @pytest.fixture
    def sample_python_documented_code(self):
        """Sample Python code with documentation."""
        return '''
"""
This is a module docstring that describes the purpose of this module.
It provides utility functions for data processing and validation.
"""

import os
import sys
from typing import List, Dict, Optional

class DataProcessor:
    """
    A class for processing various types of data.
    
    This class provides methods for cleaning, transforming,
    and validating data from different sources.
    
    Attributes:
        data_source (str): The source of the data
        processed_count (int): Number of processed items
    """
    
    def __init__(self, data_source: str):
        """
        Initialize the DataProcessor.
        
        Args:
            data_source (str): Path to the data source
        """
        self.data_source = data_source
        self.processed_count = 0
    
    def process_data(self, data: List[Dict]) -> List[Dict]:
        """
        Process a list of data dictionaries.
        
        This method cleans and transforms the input data
        according to predefined rules.
        
        Args:
            data (List[Dict]): Input data to process
            
        Returns:
            List[Dict]: Processed and cleaned data
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Process each item
        processed = []
        for item in data:
            # Clean the item
            cleaned = self._clean_item(item)
            processed.append(cleaned)
        
        self.processed_count += len(processed)
        return processed
    
    def _clean_item(self, item: Dict) -> Dict:
        """Clean a single data item (private method)."""
        # Remove empty values
        return {k: v for k, v in item.items() if v is not None}

def utility_function(value: int) -> str:
    """
    A utility function that converts integers to strings.
    
    Args:
        value (int): The integer value to convert
        
    Returns:
        str: String representation of the value
    """
    return str(value)

def undocumented_function(x, y):
    # This function has no docstring
    return x + y

class UndocumentedClass:
    # This class has no docstring
    
    def method_with_docs(self) -> None:
        """This method has documentation."""
        pass
    
    def method_without_docs(self):
        pass
'''
    
    @pytest.fixture
    def sample_javascript_documented_code(self):
        """Sample JavaScript code with JSDoc documentation."""
        return '''
/**
 * User management module
 * @module UserManager
 */

/**
 * Represents a user in the system
 * @class
 */
class User {
    /**
     * Create a user
     * @param {string} name - The user's name
     * @param {string} email - The user's email
     */
    constructor(name, email) {
        this.name = name;
        this.email = email;
    }
    
    /**
     * Get user information
     * @returns {Object} User information object
     */
    getInfo() {
        return {
            name: this.name,
            email: this.email
        };
    }
    
    // This method has no JSDoc
    updateEmail(newEmail) {
        this.email = newEmail;
    }
}

/**
 * Validates an email address
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid, false otherwise
 */
function validateEmail(email) {
    return email.includes('@');
}

// Undocumented function
function processData(data) {
    return data.map(item => item.value);
}
'''
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.doc_patterns is not None
        assert analyzer.doc_file_patterns is not None
        assert analyzer.language_patterns is not None
        
        # Check language patterns
        assert 'python' in analyzer.doc_patterns
        assert 'javascript' in analyzer.doc_patterns
        assert 'java' in analyzer.doc_patterns
        
        # Check doc file patterns
        assert 'readme_files' in analyzer.doc_file_patterns
        assert 'changelog_files' in analyzer.doc_file_patterns
        assert 'contributing_files' in analyzer.doc_file_patterns
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language('.py') == 'python'
        assert analyzer._detect_language('.js') == 'javascript'
        assert analyzer._detect_language('.java') == 'java'
        assert analyzer._detect_language('.unknown') == 'generic'
    
    def test_analyze_doc_file_quality_comprehensive(self, analyzer, sample_readme_content):
        """Test documentation file quality analysis."""
        with patch('builtins.open', mock_open(read_data=sample_readme_content)):
            test_file = Path('README.md')
            quality = analyzer._analyze_doc_file_quality(test_file)
            
            assert 0 <= quality <= 1
            assert quality > 0.5  # Should be high quality due to comprehensive content
    
    def test_analyze_doc_file_quality_minimal(self, analyzer):
        """Test documentation file quality with minimal content."""
        minimal_content = "# Project\n\nBasic description."
        
        with patch('builtins.open', mock_open(read_data=minimal_content)):
            test_file = Path('README.md')
            quality = analyzer._analyze_doc_file_quality(test_file)
            
            assert 0 <= quality <= 1
            assert quality < 0.5  # Should be lower quality
    
    def test_analyze_doc_file_quality_empty(self, analyzer):
        """Test documentation file quality with empty content."""
        with patch('builtins.open', mock_open(read_data='')):
            test_file = Path('README.md')
            quality = analyzer._analyze_doc_file_quality(test_file)
            
            assert quality == 0.0
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_doc_file_quality_error(self, mock_open, analyzer):
        """Test documentation file quality with IO error."""
        test_file = Path('nonexistent.md')
        quality = analyzer._analyze_doc_file_quality(test_file)
        assert quality == 0.0
    
    def test_is_comment_line(self, analyzer):
        """Test comment line detection."""
        # Python comments
        assert analyzer._is_comment_line('# This is a comment', 'python') == True
        assert analyzer._is_comment_line('    # Indented comment', 'python') == True
        assert analyzer._is_comment_line('x = 5  # Inline comment', 'python') == False  # Not starting with #
        
        # JavaScript comments
        assert analyzer._is_comment_line('// This is a comment', 'javascript') == True
        assert analyzer._is_comment_line('/* Block comment */', 'javascript') == True
        assert analyzer._is_comment_line('* Inside block comment', 'javascript') == True
        
        # Java comments
        assert analyzer._is_comment_line('// Java comment', 'java') == True
        assert analyzer._is_comment_line('/* Java block comment */', 'java') == True
    
    def test_is_function_documented_python(self, analyzer):
        """Test Python function documentation detection."""
        import re
        
        # Function with docstring
        documented_func = '''def test_func():
    """This function has a docstring."""
    pass'''
        
        func_match = re.search(r'def\s+(\w+)\s*\(', documented_func)
        doc_patterns = analyzer.doc_patterns['python']
        
        is_documented = analyzer._is_function_documented(documented_func, func_match, doc_patterns, 'python')
        assert is_documented == True
        
        # Function without docstring
        undocumented_func = '''def test_func():
    pass'''
        
        func_match = re.search(r'def\s+(\w+)\s*\(', undocumented_func)
        is_documented = analyzer._is_function_documented(undocumented_func, func_match, doc_patterns, 'python')
        assert is_documented == False
    
    def test_is_class_documented_python(self, analyzer):
        """Test Python class documentation detection."""
        import re
        
        # Class with docstring
        documented_class = '''class TestClass:
    """This class has a docstring."""
    pass'''
        
        class_match = re.search(r'class\s+(\w+)', documented_class)
        doc_patterns = analyzer.doc_patterns['python']
        
        is_documented = analyzer._is_class_documented(documented_class, class_match, doc_patterns, 'python')
        assert is_documented == True
        
        # Class without docstring
        undocumented_class = '''class TestClass:
    pass'''
        
        class_match = re.search(r'class\s+(\w+)', undocumented_class)
        is_documented = analyzer._is_class_documented(undocumented_class, class_match, doc_patterns, 'python')
        assert is_documented == False
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_documentation_python(self, analyzer, sample_python_documented_code):
        """Test Python file documentation analysis."""
        with patch('builtins.open', mock_open(read_data=sample_python_documented_code)):
            test_file = Path('test.py')
            result = analyzer._analyze_file_documentation(test_file)
            
            assert result is not None
            assert result['language'] == 'python'
            assert result['total_lines'] > 0
            assert result['comment_lines'] > 0
            assert result['function_count'] > 0
            assert result['documented_functions'] > 0
            assert result['class_count'] > 0
            assert result['documented_classes'] > 0
            assert result['has_module_doc'] == True
            assert len(result['undocumented_items']) > 0  # Should find undocumented items
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_documentation_javascript(self, analyzer, sample_javascript_documented_code):
        """Test JavaScript file documentation analysis."""
        with patch('builtins.open', mock_open(read_data=sample_javascript_documented_code)):
            test_file = Path('test.js')
            result = analyzer._analyze_file_documentation(test_file)
            
            assert result is not None
            assert result['language'] == 'javascript'
            assert result['total_lines'] > 0
            assert result['comment_lines'] > 0
            assert result['function_count'] > 0
            assert result['class_count'] > 0
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_file_documentation_error(self, mock_open, analyzer):
        """Test file documentation analysis with IO error."""
        test_file = Path('nonexistent.py')
        result = analyzer._analyze_file_documentation(test_file)
        assert result is None
    
    @patch('builtins.open', mock_open(read_data=''))
    def test_analyze_file_documentation_empty(self, analyzer):
        """Test analysis of empty file."""
        test_file = Path('empty.py')
        result = analyzer._analyze_file_documentation(test_file)
        assert result is None
    
    def test_analyze_code_documentation(self, analyzer, sample_python_documented_code):
        """Test code documentation analysis."""
        with patch('builtins.open', mock_open(read_data=sample_python_documented_code)):
            test_files = [Path('test1.py'), Path('test2.py')]
            result = analyzer._analyze_code_documentation(test_files)
            
            assert 'total_functions' in result
            assert 'documented_functions' in result
            assert 'total_classes' in result
            assert 'documented_classes' in result
            assert 'total_modules' in result
            assert 'documented_modules' in result
            assert 'comment_density' in result
            assert 'type_hint_coverage' in result
            assert 'undocumented_items' in result
            
            assert result['total_functions'] > 0
            assert result['documented_functions'] > 0
            assert result['total_classes'] > 0
            assert result['documented_classes'] > 0
            assert 0 <= result['comment_density'] <= 1
    
    def test_analyze_documentation_files(self, analyzer, sample_readme_content):
        """Test documentation files analysis."""
        # Mock file system with README.md
        def mock_rglob(self, pattern):
            if pattern == '*':
                return [Path('README.md'), Path('src/main.py')]
            return []
        
        with patch('builtins.open', mock_open(read_data=sample_readme_content)):
            with patch.object(Path, 'rglob', mock_rglob):
                with patch.object(Path, 'is_file', return_value=True):
                    repo_path = Path('/fake/repo')
                    result = analyzer._analyze_documentation_files(repo_path)
                    
                    assert 'files_found' in result
                    assert 'total_score' in result
                    assert 'max_possible_score' in result
                    assert 'file_qualities' in result
                    assert 'missing_docs' in result
                    
                    assert result['total_score'] > 0
                    assert result['max_possible_score'] > 0
                    assert 'readme_files' in result['files_found']
    
    def test_calculate_documentation_metrics(self, analyzer):
        """Test documentation metrics calculation."""
        doc_files_analysis = {
            'total_score': 8.0,
            'max_possible_score': 10.0,
            'files_found': {
                'readme_files': [Path('README.md')],
                'changelog_files': [Path('CHANGELOG.md')]
            },
            'file_qualities': {
                'README.md': 0.8,
                'CHANGELOG.md': 0.6
            }
        }
        
        code_doc_analysis = {
            'total_functions': 10,
            'documented_functions': 7,
            'total_classes': 5,
            'documented_classes': 4,
            'comment_density': 0.15
        }
        
        repo_path = Path('/fake/repo')
        source_files = [Path('test1.py'), Path('test2.py')]
        
        metrics = analyzer._calculate_documentation_metrics(
            doc_files_analysis, code_doc_analysis, repo_path, source_files
        )
        
        assert 'overall_score' in metrics
        assert 'readme_quality' in metrics
        assert 'docstring_coverage' in metrics
        assert 'api_doc_coverage' in metrics
        assert 'has_changelog' in metrics
        assert 'has_contributing_guide' in metrics
        assert 'doc_files_count' in metrics
        
        assert 0 <= metrics['overall_score'] <= 10
        assert 0 <= metrics['readme_quality'] <= 10
        assert 0 <= metrics['docstring_coverage'] <= 1
        assert 0 <= metrics['api_doc_coverage'] <= 1
        assert metrics['has_changelog'] == True
        assert metrics['doc_files_count'] == 2
    
    @patch('builtins.open', mock_open())
    def test_analyze_integration(self, analyzer, sample_readme_content, sample_python_documented_code):
        """Test full analysis integration."""
        def mock_rglob(self, pattern):
            if pattern == '*':
                return [Path('README.md'), Path('src/main.py')]
            return []
        
        with patch('builtins.open', mock_open(read_data=sample_readme_content)):
            with patch.object(Path, 'rglob', mock_rglob):
                with patch.object(Path, 'is_file', return_value=True):
                    repo_path = Path('/fake/repo')
                    source_files = [Path('test1.py'), Path('test2.py')]
                    
                    # Mock the file content based on the file being opened
                    def side_effect(*args, **kwargs):
                        if 'README.md' in str(args[0]):
                            return mock_open(read_data=sample_readme_content)(*args, **kwargs)
                        else:
                            return mock_open(read_data=sample_python_documented_code)(*args, **kwargs)
                    
                    with patch('builtins.open', side_effect=side_effect):
                        result = analyzer.analyze(repo_path, source_files)
                        
                        assert result is not None
                        assert hasattr(result, 'score')
                        assert hasattr(result, 'readme_quality')
                        assert hasattr(result, 'docstring_coverage')
                        assert hasattr(result, 'api_doc_coverage')
                        assert hasattr(result, 'has_changelog')
                        assert hasattr(result, 'has_contributing_guide')
                        assert hasattr(result, 'doc_files_count')
                        
                        assert 0 <= result.score <= 10
                        assert 0 <= result.readme_quality <= 10
                        assert 0 <= result.docstring_coverage <= 1
    
    def test_empty_source_files(self, analyzer):
        """Test analysis with empty source files."""
        def mock_rglob(self, pattern):
            return []
        
        with patch.object(Path, 'rglob', mock_rglob):
            repo_path = Path('/fake/repo')
            source_files = []
            result = analyzer.analyze(repo_path, source_files)
            
            assert result is not None
            assert result.score >= 0
    
    def test_doc_file_pattern_matching(self, analyzer):
        """Test documentation file pattern matching."""
        patterns = analyzer.doc_file_patterns
        
        # Test README patterns
        readme_patterns = patterns['readme_files']['patterns']
        assert any(re.search(pattern, 'README.md') for pattern in readme_patterns)
        assert any(re.search(pattern, 'readme.txt') for pattern in readme_patterns)
        
        # Test CHANGELOG patterns
        changelog_patterns = patterns['changelog_files']['patterns']
        assert any(re.search(pattern, 'CHANGELOG.md') for pattern in changelog_patterns)
        assert any(re.search(pattern, 'CHANGES.rst') for pattern in changelog_patterns)
        
        # Test CONTRIBUTING patterns
        contrib_patterns = patterns['contributing_files']['patterns']
        assert any(re.search(pattern, 'CONTRIBUTING.md') for pattern in contrib_patterns)
    
    def test_quality_indicators_detection(self, analyzer, sample_readme_content):
        """Test quality indicators in documentation."""
        quality = analyzer._analyze_doc_file_quality(Path('fake'))
        
        # Mock the file reading to return our sample content
        with patch('builtins.open', mock_open(read_data=sample_readme_content)):
            quality = analyzer._analyze_doc_file_quality(Path('README.md'))
            
            assert quality > 0.5  # Should detect multiple quality indicators
            # The sample has: installation, usage, API docs, links, code examples, headers


if __name__ == '__main__':
    pytest.main([__file__])
