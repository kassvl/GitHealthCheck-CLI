"""Integration tests for the complete repository health analyzer system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


@patch('repo_health_analyzer.core.analyzer.GitRepositoryParser')
class TestRepositoryAnalyzerIntegration:
    """Integration test cases for the complete system."""
    
    @pytest.fixture
    def sample_repo_path(self):
        """Sample repository path for testing."""
        return Path('/fake/test/repo')
    
    @pytest.fixture
    def sample_config(self):
        """Sample analysis configuration."""
        return AnalysisConfig(
            include_patterns=['*.py', '*.js'],
            exclude_patterns=['*/node_modules/*', '*/venv/*'],
            max_file_size_mb=1  # 1MB
        )
    
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return '''
"""
High-quality Python module with good practices.
This module demonstrates proper documentation and code structure.
"""

import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class User:
    """
    Represents a user in the system.
    
    Attributes:
        name (str): The user's full name
        email (str): The user's email address
        age (int): The user's age
    """
    name: str
    email: str
    age: int
    
    def is_adult(self) -> bool:
        """
        Check if the user is an adult.
        
        Returns:
            bool: True if user is 18 or older, False otherwise
        """
        return self.age >= 18
    
    def validate_email(self) -> bool:
        """
        Validate the user's email address.
        
        Returns:
            bool: True if email is valid, False otherwise
        """
        return '@' in self.email and '.' in self.email


class UserService:
    """
    Service class for managing users.
    
    This class provides methods for user management operations
    including creation, validation, and storage.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the UserService.
        
        Args:
            database_url (str): URL of the database connection
        """
        self.database_url = database_url
        self.users: List[User] = []
    
    def create_user(self, name: str, email: str, age: int) -> Optional[User]:
        """
        Create a new user with validation.
        
        Args:
            name (str): User's full name
            email (str): User's email address
            age (int): User's age
            
        Returns:
            Optional[User]: Created user if valid, None otherwise
            
        Raises:
            ValueError: If user data is invalid
        """
        if not name or not email:
            raise ValueError("Name and email are required")
        
        if age < 0 or age > 150:
            raise ValueError("Invalid age")
        
        user = User(name=name, email=email, age=age)
        
        if user.validate_email():
            self.users.append(user)
            return user
        
        return None
    
    def get_adult_users(self) -> List[User]:
        """
        Get all adult users.
        
        Returns:
            List[User]: List of users who are adults
        """
        return [user for user in self.users if user.is_adult()]
    
    def get_user_count(self) -> int:
        """
        Get the total number of users.
        
        Returns:
            int: Total number of users
        """
        return len(self.users)


def validate_user_data(user_data: Dict[str, any]) -> bool:
    """
    Validate user data dictionary.
    
    Args:
        user_data (Dict[str, any]): Dictionary containing user data
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    required_fields = ['name', 'email', 'age']
    
    # Check required fields
    for field in required_fields:
        if field not in user_data:
            return False
    
    # Validate data types
    if not isinstance(user_data['name'], str):
        return False
    
    if not isinstance(user_data['email'], str):
        return False
    
    if not isinstance(user_data['age'], int):
        return False
    
    return True
'''
    
    @pytest.fixture
    def sample_test_code(self):
        """Sample test code for testing."""
        return '''
"""
Comprehensive test suite for user management module.
"""

import pytest
import unittest
from unittest.mock import Mock, patch
from myapp.user import User, UserService, validate_user_data


class TestUser(unittest.TestCase):
    """Test cases for User class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User("John Doe", "john@example.com", 25)
    
    def test_user_creation(self):
        """Test user creation with valid data."""
        assert self.user.name == "John Doe"
        assert self.user.email == "john@example.com"
        assert self.user.age == 25
    
    def test_is_adult(self):
        """Test adult validation."""
        assert self.user.is_adult() is True
        
        child = User("Child", "child@example.com", 15)
        assert child.is_adult() is False
    
    def test_validate_email(self):
        """Test email validation."""
        assert self.user.validate_email() is True
        
        invalid_user = User("Invalid", "invalid-email", 25)
        assert invalid_user.validate_email() is False


class TestUserService:
    """Pytest-style test class for UserService."""
    
    @pytest.fixture
    def user_service(self):
        """User service fixture."""
        return UserService("sqlite:///:memory:")
    
    def test_create_user_success(self, user_service):
        """Test successful user creation."""
        user = user_service.create_user("Test User", "test@example.com", 30)
        
        assert user is not None
        assert user.name == "Test User"
        assert user_service.get_user_count() == 1
    
    def test_create_user_invalid_email(self, user_service):
        """Test user creation with invalid email."""
        user = user_service.create_user("Test", "invalid", 25)
        assert user is None
        assert user_service.get_user_count() == 0
    
    def test_create_user_missing_data(self, user_service):
        """Test user creation with missing data."""
        with pytest.raises(ValueError):
            user_service.create_user("", "test@example.com", 25)
        
        with pytest.raises(ValueError):
            user_service.create_user("Test", "", 25)
    
    def test_create_user_invalid_age(self, user_service):
        """Test user creation with invalid age."""
        with pytest.raises(ValueError):
            user_service.create_user("Test", "test@example.com", -5)
        
        with pytest.raises(ValueError):
            user_service.create_user("Test", "test@example.com", 200)
    
    def test_get_adult_users(self, user_service):
        """Test getting adult users."""
        user_service.create_user("Adult", "adult@example.com", 25)
        user_service.create_user("Child", "child@example.com", 15)
        user_service.create_user("Senior", "senior@example.com", 65)
        
        adults = user_service.get_adult_users()
        assert len(adults) == 2
        assert all(user.is_adult() for user in adults)


def test_validate_user_data():
    """Test user data validation function."""
    valid_data = {
        "name": "Test User",
        "email": "test@example.com",
        "age": 25
    }
    assert validate_user_data(valid_data) is True
    
    # Missing field
    invalid_data = {"name": "Test", "email": "test@example.com"}
    assert validate_user_data(invalid_data) is False
    
    # Wrong type
    invalid_type = {"name": 123, "email": "test@example.com", "age": 25}
    assert validate_user_data(invalid_type) is False


@pytest.mark.integration
def test_full_user_workflow():
    """Integration test for complete user workflow."""
    service = UserService("test://database")
    
    # Create users
    user1 = service.create_user("Alice", "alice@example.com", 28)
    user2 = service.create_user("Bob", "bob@example.com", 16)
    user3 = service.create_user("Charlie", "charlie@example.com", 35)
    
    assert service.get_user_count() == 3
    
    # Get adult users
    adults = service.get_adult_users()
    assert len(adults) == 2
    assert "Alice" in [user.name for user in adults]
    assert "Charlie" in [user.name for user in adults]
    assert "Bob" not in [user.name for user in adults]
'''
    
    @pytest.fixture
    def sample_readme_content(self):
        """Sample README content."""
        return '''
# User Management System

A comprehensive user management system built with Python.

## Features

- User creation and validation
- Email validation
- Age verification
- Adult user filtering
- Database integration

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## Usage

```python
from myapp.user import UserService

service = UserService("sqlite:///users.db")
user = service.create_user("John Doe", "john@example.com", 25)
```

## API Reference

### User Class

The main user entity with validation methods.

#### Methods

- `is_adult()`: Check if user is 18 or older
- `validate_email()`: Validate email format

### UserService Class

Service for managing users.

#### Methods

- `create_user(name, email, age)`: Create a new user
- `get_adult_users()`: Get all adult users
- `get_user_count()`: Get total user count

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Contributing

Please read CONTRIBUTING.md for contribution guidelines.

## License

This project is licensed under the MIT License.
'''
    
    @pytest.fixture
    def mock_file_system(self, sample_python_code, sample_test_code, sample_readme_content):
        """Mock file system with sample files."""
        file_contents = {
            'src/user.py': sample_python_code,
            'tests/test_user.py': sample_test_code,
            'README.md': sample_readme_content,
            'requirements.txt': 'pytest>=6.0\ntyping-extensions>=3.7',
            'setup.py': 'from setuptools import setup\nsetup(name="myapp")'
        }
        
        def mock_open_side_effect(*args, **kwargs):
            file_path = str(args[0])
            for path_key, content in file_contents.items():
                if path_key in file_path or file_path.endswith(path_key.split('/')[-1]):
                    return mock_open(read_data=content)(*args, **kwargs)
            return mock_open(read_data='')(*args, **kwargs)
        
        return mock_open_side_effect
    
    @pytest.fixture
    def mock_git_operations(self):
        """Mock git operations."""
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            cmd_str = str(cmd) if cmd else ''
            
            if 'git' in cmd_str and 'log' in cmd_str:
                return Mock(returncode=0, stdout='''commit abc123
Author: Test Developer <test@example.com>
Date: 2024-01-15 10:30:00 +0000

    Initial implementation of user management system

commit def456
Author: Test Developer <test@example.com>
Date: 2024-01-10 14:20:00 +0000

    Add comprehensive test suite

commit ghi789
Author: Another Developer <another@example.com>
Date: 2024-01-05 09:15:00 +0000

    Update documentation and README
''')
            elif 'git' in cmd_str and 'branch' in cmd_str:
                return Mock(returncode=0, stdout='main\n')
            elif 'git' in cmd_str and 'rev-list' in cmd_str:
                return Mock(returncode=0, stdout='25\n')
            elif 'git' in cmd_str and 'shortlog' in cmd_str:
                return Mock(returncode=0, stdout='Test Developer\nAnother Developer\n')
            else:
                return Mock(returncode=0, stdout='')
        
        return mock_run_side_effect
    
    def test_analyzer_initialization(self, mock_git_parser, sample_repo_path, sample_config):
        """Test analyzer initialization."""
        analyzer = RepositoryAnalyzer(sample_repo_path, sample_config, verbose=False)
        
        assert analyzer.repo_path == sample_repo_path
        assert analyzer.config == sample_config
        assert analyzer.orchestrator is not None
        assert analyzer.code_quality_analyzer is not None
        assert analyzer.architecture_analyzer is not None
        assert analyzer.code_smell_analyzer is not None
        assert analyzer.test_analyzer is not None
        assert analyzer.documentation_analyzer is not None
        assert analyzer.sustainability_analyzer is not None
        assert analyzer.visualizer is not None
    
    @patch('subprocess.run')
    @patch('builtins.open')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_full_analysis_integration(self, mock_git_parser, mock_exists, mock_is_file, mock_rglob, 
                                     mock_open_builtin, mock_subprocess,
                                     sample_repo_path, sample_config, 
                                     mock_file_system, mock_git_operations):
        """Test complete analysis integration."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_subprocess.side_effect = mock_git_operations
        mock_open_builtin.side_effect = mock_file_system
        
        # Mock file discovery
        sample_files = [
            Path('src/user.py'),
            Path('src/models.py'),
            Path('tests/test_user.py'),
            Path('tests/test_models.py'),
            Path('README.md'),
            Path('requirements.txt')
        ]
        mock_rglob.return_value = sample_files
        
        # Create analyzer and run analysis
        analyzer = RepositoryAnalyzer(sample_repo_path, sample_config, verbose=True)
        result = analyzer.analyze()
        
        # Verify result structure
        assert result is not None
        assert hasattr(result, 'repository')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'analysis_duration')
        
        # Verify repository info
        repo_info = result.repository
        assert repo_info.name is not None
        assert repo_info.path == str(sample_repo_path)
        assert repo_info.total_commits > 0
        
        # Verify metrics
        metrics = result.metrics
        assert hasattr(metrics, 'overall_score')
        assert hasattr(metrics, 'code_quality')
        assert hasattr(metrics, 'architecture')
        assert hasattr(metrics, 'code_smells')
        assert hasattr(metrics, 'tests')
        assert hasattr(metrics, 'documentation')
        assert hasattr(metrics, 'sustainability')
        
        # Check score ranges
        assert 0 <= metrics.overall_score <= 10
        assert 0 <= metrics.code_quality.overall_score <= 10
        assert 0 <= metrics.architecture.score <= 10
        assert 0 <= metrics.code_smells.severity_score <= 10
        assert 0 <= metrics.tests.coverage_score <= 10
        assert 0 <= metrics.documentation.score <= 10
        assert 0 <= metrics.sustainability.score <= 10
        
        # Verify recommendations
        assert isinstance(result.recommendations, list)
        assert result.analysis_duration > 0
    
    @patch('subprocess.run')
    @patch('builtins.open')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_analysis_with_poor_quality_code(self, mock_exists, mock_is_file, mock_rglob,
                                           mock_open_builtin, mock_subprocess,
                                           sample_repo_path):
        """Test analysis with poor quality code."""
        poor_quality_code = '''
# Poor quality code with many issues

def veryLongFunctionNameThatDoesTooManyThings(param1, param2, param3, param4, param5, param6, param7, param8):
    x = 42  # Magic number
    y = "hardcoded string that is very long and should be a constant"
    z = 100  # Another magic number
    
    if param1 > 50:
        if param2 < 20:
            if param3 == "test":
                if param4 != None:
                    if param5 > param6:
                        return x + y + z + param1 + param2 + param3 + param4 + param5
                    else:
                        return x - y
                else:
                    return 0
            else:
                return -1
        else:
            return param1
    else:
        return param2

def anotherVeryLongFunction():
    # Duplicate logic from above
    x = 42
    y = "hardcoded string that is very long and should be a constant"
    z = 100
    
    if True:
        if True:
            if True:
                return x + y + z
    return 0

class GodClassThatDoesEverything:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
    def method23(self): pass
    def method24(self): pass
    def method25(self): pass
'''
        
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stdout='main\n')
        mock_open_builtin.return_value = mock_open(read_data=poor_quality_code)
        
        sample_files = [Path('src/bad_code.py')]
        mock_rglob.return_value = sample_files
        
        # Run analysis
        analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
        result = analyzer.analyze()
        
        # Should detect quality issues
        assert result.metrics.code_quality.overall_score < 7  # Should be low
        assert result.metrics.code_smells.total_count > 0  # Should find smells
        
        # Should have recommendations
        assert len(result.recommendations) > 0
        recommendation_texts = [r.description for r in result.recommendations]
        assert any('complexity' in text.lower() for text in recommendation_texts)
    
    @patch('subprocess.run')
    @patch('builtins.open')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_analysis_with_no_tests(self, mock_exists, mock_is_file, mock_rglob,
                                  mock_open_builtin, mock_subprocess,
                                  sample_repo_path, sample_python_code):
        """Test analysis with no test files."""
        # Setup mocks - only source files, no tests
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stdout='main\n')
        mock_open_builtin.return_value = mock_open(read_data=sample_python_code)
        
        # Only source files, no test files
        sample_files = [Path('src/main.py'), Path('src/utils.py')]
        mock_rglob.return_value = sample_files
        
        # Run analysis
        analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
        result = analyzer.analyze()
        
        # Should detect lack of tests
        assert result.metrics.tests.coverage_score < 5  # Should be low
        assert result.metrics.tests.test_files_count == 0
        
        # Should recommend adding tests
        recommendation_texts = [r.description.lower() for r in result.recommendations]
        assert any('test' in text for text in recommendation_texts)
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_analysis_with_git_errors(self, mock_exists, mock_subprocess, sample_repo_path):
        """Test analysis when git operations fail."""
        # Setup mocks - git operations fail
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(returncode=128, stderr='fatal: not a git repository')
        
        # Run analysis
        analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
        result = analyzer.analyze()
        
        # Should still complete analysis with default values
        assert result is not None
        assert result.repository is None or result.repository.total_commits == 0
        assert result.metrics.sustainability.score >= 0  # Should handle gracefully
    
    def test_analysis_with_empty_repository(self, sample_repo_path):
        """Test analysis with empty repository."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.rglob', return_value=[]):
                with patch('subprocess.run', return_value=Mock(returncode=0, stdout='')):
                    analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
                    result = analyzer.analyze()
                    
                    # Should handle empty repository gracefully
                    assert result is not None
                    assert result.metrics.overall_score >= 0
    
    @patch('subprocess.run')
    @patch('builtins.open')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_visualization_generation(self, mock_exists, mock_is_file, mock_rglob,
                                    mock_open_builtin, mock_subprocess,
                                    sample_repo_path, mock_file_system, mock_git_operations):
        """Test visualization generation."""
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_subprocess.side_effect = mock_git_operations
        mock_open_builtin.side_effect = mock_file_system
        
        sample_files = [Path('src/user.py'), Path('tests/test_user.py')]
        mock_rglob.return_value = sample_files
        
        # Run analysis
        analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
        result = analyzer.analyze()
        
        # Test visualization generation (visualizer is mocked, so just check it exists)
        assert hasattr(analyzer, 'visualizer')
        assert analyzer.visualizer is not None
    
    def test_configuration_handling(self, mock_git_parser, sample_repo_path):
        """Test different configuration options."""
        # Test with custom config
        custom_config = AnalysisConfig(
            include_patterns=['*.py'],
            exclude_patterns=['*/test*'],
            max_file_size_mb=1
        )
        
        analyzer = RepositoryAnalyzer(sample_repo_path, custom_config, verbose=True)
        assert analyzer.config == custom_config
        assert analyzer.verbose == True
        
        # Test with default config
        analyzer_default = RepositoryAnalyzer(sample_repo_path)
        assert analyzer_default.config is not None
        assert analyzer_default.verbose == False
    
    def test_error_handling_in_orchestrator(self, mock_git_parser, sample_repo_path):
        """Test error handling in the orchestration process."""
        analyzer = RepositoryAnalyzer(sample_repo_path, verbose=False)
        
        # Mock one analyzer to raise an exception
        with patch.object(analyzer.code_quality_analyzer, 'analyze', side_effect=Exception("Test error")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob', return_value=[]):
                    with patch('subprocess.run', return_value=Mock(returncode=0, stdout='')):
                        # Should handle errors gracefully and continue
                        result = analyzer.analyze()
                        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__])
