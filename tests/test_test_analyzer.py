"""Tests for Test Analyzer."""

import re
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from collections import Counter
from repo_health_analyzer.core.analyzers.test_analyzer import TestCodeAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestTestAnalyzer:
    """Test cases for Test Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return TestCodeAnalyzer(config)
    
    @pytest.fixture
    def sample_python_test_code(self):
        """Sample Python test code."""
        return '''
"""Test module for user management."""

import pytest
import unittest
from unittest.mock import Mock, patch
from myapp.user import User, UserService


class TestUser(unittest.TestCase):
    """Test cases for User class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User("John Doe", "john@example.com")
    
    def test_user_creation(self):
        """Test user creation."""
        assert self.user.name == "John Doe"
        assert self.user.email == "john@example.com"
    
    def test_user_validation(self):
        """Test user validation."""
        assert self.user.is_valid()
        
        invalid_user = User("", "invalid-email")
        assert not invalid_user.is_valid()
    
    def tearDown(self):
        """Clean up after tests."""
        self.user = None


class TestUserService:
    """Pytest-style test class."""
    
    @pytest.fixture
    def user_service(self):
        """User service fixture."""
        return UserService()
    
    @pytest.mark.parametrize("name,email,expected", [
        ("John", "john@test.com", True),
        ("", "john@test.com", False),
        ("John", "invalid", False)
    ])
    def test_create_user(self, user_service, name, email, expected):
        """Test user creation with parameters."""
        result = user_service.create_user(name, email)
        assert bool(result) == expected
    
    def test_user_not_found(self, user_service):
        """Test user not found scenario."""
        with pytest.raises(ValueError):
            user_service.get_user(999)
    
    @patch('myapp.database.Database.save')
    def test_save_user(self, mock_save, user_service):
        """Test user saving with mock."""
        user = User("Test", "test@example.com")
        user_service.save_user(user)
        
        mock_save.assert_called_once_with(user)
        assert mock_save.call_count == 1


def test_standalone_function():
    """Standalone test function."""
    result = 2 + 2
    assert result == 4


@pytest.mark.integration
def test_integration_scenario():
    """Integration test."""
    service = UserService()
    user = service.create_user("Integration", "test@integration.com")
    assert user is not None
    assert service.get_user_count() == 1
'''
    
    @pytest.fixture
    def sample_javascript_test_code(self):
        """Sample JavaScript test code."""
        return '''
/**
 * Test suite for user management
 */

const { expect } = require('chai');
const sinon = require('sinon');
const User = require('../src/user');
const UserService = require('../src/userService');

describe('User', () => {
    let user;
    
    beforeEach(() => {
        user = new User('John Doe', 'john@example.com');
    });
    
    afterEach(() => {
        user = null;
    });
    
    describe('constructor', () => {
        it('should create user with name and email', () => {
            expect(user.name).to.equal('John Doe');
            expect(user.email).to.equal('john@example.com');
        });
        
        it('should throw error for invalid email', () => {
            expect(() => new User('John', 'invalid')).to.throw();
        });
    });
    
    describe('validation', () => {
        it('should validate correct user data', () => {
            expect(user.isValid()).to.be.true;
        });
        
        it('should reject empty name', () => {
            user.name = '';
            expect(user.isValid()).to.be.false;
        });
    });
});

describe('UserService', () => {
    let userService;
    let mockDatabase;
    
    beforeEach(() => {
        mockDatabase = sinon.createStubInstance(Database);
        userService = new UserService(mockDatabase);
    });
    
    describe('createUser', () => {
        it('should create and save user', async () => {
            const userData = { name: 'Test User', email: 'test@example.com' };
            mockDatabase.save.resolves({ id: 1, ...userData });
            
            const result = await userService.createUser(userData);
            
            expect(result).to.have.property('id', 1);
            expect(mockDatabase.save.calledOnce).to.be.true;
        });
        
        it('should handle database errors', async () => {
            mockDatabase.save.rejects(new Error('Database error'));
            
            try {
                await userService.createUser({ name: 'Test', email: 'test@example.com' });
                expect.fail('Should have thrown error');
            } catch (error) {
                expect(error.message).to.include('Database error');
            }
        });
    });
    
    describe('getUser', () => {
        it('should retrieve user by id', async () => {
            const userId = 1;
            const expectedUser = { id: userId, name: 'John', email: 'john@example.com' };
            mockDatabase.findById.resolves(expectedUser);
            
            const result = await userService.getUser(userId);
            
            expect(result).to.deep.equal(expectedUser);
            expect(mockDatabase.findById.calledWith(userId)).to.be.true;
        });
    });
});

// Standalone test
test('utility function test', () => {
    const result = addNumbers(2, 3);
    expect(result).toBe(5);
});
'''
    
    @pytest.fixture
    def sample_java_test_code(self):
        """Sample Java test code."""
        return '''
package com.example.user;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.mockito.Mock;
import org.mockito.MockitoExtensions;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtensions.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    private UserService userService;
    
    @BeforeEach
    void setUp() {
        userService = new UserService(userRepository);
    }
    
    @AfterEach
    void tearDown() {
        userService = null;
    }
    
    @Test
    @DisplayName("Should create user successfully")
    void testCreateUserSuccess() {
        // Given
        String name = "John Doe";
        String email = "john@example.com";
        User expectedUser = new User(name, email);
        when(userRepository.save(any(User.class))).thenReturn(expectedUser);
        
        // When
        User result = userService.createUser(name, email);
        
        // Then
        assertNotNull(result);
        assertEquals(name, result.getName());
        assertEquals(email, result.getEmail());
        verify(userRepository).save(any(User.class));
    }
    
    @Test
    void testCreateUserWithInvalidEmail() {
        // Given
        String name = "John Doe";
        String invalidEmail = "invalid-email";
        
        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            userService.createUser(name, invalidEmail);
        });
        
        verify(userRepository, never()).save(any(User.class));
    }
    
    @Test
    void testGetUserById() {
        // Given
        Long userId = 1L;
        User expectedUser = new User("John", "john@example.com");
        when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));
        
        // When
        Optional<User> result = userService.getUserById(userId);
        
        // Then
        assertTrue(result.isPresent());
        assertEquals(expectedUser, result.get());
    }
    
    @Test
    void testGetUserByIdNotFound() {
        // Given
        Long userId = 999L;
        when(userRepository.findById(userId)).thenReturn(Optional.empty());
        
        // When
        Optional<User> result = userService.getUserById(userId);
        
        // Then
        assertFalse(result.isPresent());
    }
}

class UserTest {
    
    private User user;
    
    @BeforeEach
    void setUp() {
        user = new User("John Doe", "john@example.com");
    }
    
    @Test
    void testUserCreation() {
        assertNotNull(user);
        assertEquals("John Doe", user.getName());
        assertEquals("john@example.com", user.getEmail());
    }
    
    @Test
    void testUserValidation() {
        assertTrue(user.isValid());
        
        User invalidUser = new User("", "invalid");
        assertFalse(invalidUser.isValid());
    }
}
'''
    
    @pytest.fixture
    def sample_source_files(self):
        """Sample source files for testing."""
        return [
            Path('src/user.py'),
            Path('src/user_service.py'),
            Path('src/database.py'),
            Path('src/utils.py'),
            Path('test_user.py'),
            Path('test_user_service.py'),
            Path('tests/test_integration.py'),
            Path('tests/conftest.py')
        ]
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.test_patterns is not None
        assert analyzer.framework_patterns is not None
        
        # Check test patterns
        patterns = analyzer.test_patterns
        assert 'file_patterns' in patterns
        assert 'function_patterns' in patterns
        assert 'assertion_patterns' in patterns
        
        # Check language support
        assert 'python' in patterns['file_patterns']
        assert 'javascript' in patterns['file_patterns']
        assert 'java' in patterns['file_patterns']
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language('.py') == 'python'
        assert analyzer._detect_language('.js') == 'javascript'
        assert analyzer._detect_language('.java') == 'java'
        assert analyzer._detect_language('.cs') == 'csharp'
        assert analyzer._detect_language('.unknown') == 'generic'
    
    def test_separate_test_files(self, analyzer, sample_source_files):
        """Test separation of test files from source files."""
        test_files, source_files = analyzer._separate_test_files(sample_source_files)
        
        # Check test files
        test_file_names = [f.name for f in test_files]
        assert 'test_user.py' in test_file_names
        assert 'test_user_service.py' in test_file_names
        assert 'test_integration.py' in test_file_names
        assert 'conftest.py' in test_file_names
        
        # Check source files
        source_file_names = [f.name for f in source_files]
        assert 'user.py' in source_file_names
        assert 'user_service.py' in source_file_names
        assert 'database.py' in source_file_names
        assert 'utils.py' in source_file_names
        
        # Ensure no overlap
        assert len(set(test_file_names) & set(source_file_names)) == 0
    
    @patch('builtins.open', mock_open())
    def test_analyze_single_test_file_python(self, analyzer, sample_python_test_code):
        """Test single Python test file analysis."""
        with patch('builtins.open', mock_open(read_data=sample_python_test_code)):
            test_file = Path('test_user.py')
            result = analyzer._analyze_single_test_file(test_file)
            
            assert result is not None
            assert result['language'] == 'python'
            assert result['total_lines'] > 0
            assert result['test_functions'] > 0
            assert result['test_classes'] > 0
            assert result['assertions'] > 0
            assert result['setup_teardown'] > 0  # setUp, tearDown, fixtures
            
            # Should detect multiple test methods
            assert result['test_functions'] >= 5
            assert result['test_classes'] >= 2  # TestUser, TestUserService
    
    @patch('builtins.open', mock_open())
    def test_analyze_single_test_file_javascript(self, analyzer, sample_javascript_test_code):
        """Test single JavaScript test file analysis."""
        with patch('builtins.open', mock_open(read_data=sample_javascript_test_code)):
            test_file = Path('user.test.js')
            result = analyzer._analyze_single_test_file(test_file)
            
            assert result is not None
            assert result['language'] == 'javascript'
            assert result['total_lines'] > 0
            assert result['test_functions'] > 0  # it(), test(), describe()
            assert result['assertions'] > 0  # expect() calls
            assert result['setup_teardown'] > 0  # beforeEach, afterEach
    
    @patch('builtins.open', mock_open())
    def test_analyze_single_test_file_java(self, analyzer, sample_java_test_code):
        """Test single Java test file analysis."""
        with patch('builtins.open', mock_open(read_data=sample_java_test_code)):
            test_file = Path('UserServiceTest.java')
            result = analyzer._analyze_single_test_file(test_file)
            
            assert result is not None
            assert result['language'] == 'java'
            assert result['total_lines'] > 0
            assert result['test_functions'] > 0  # @Test methods
            assert result['assertions'] > 0  # assert* calls
            assert result['setup_teardown'] > 0  # @BeforeEach, @AfterEach
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_single_test_file_error(self, mock_open, analyzer):
        """Test single test file analysis with IO error."""
        test_file = Path('nonexistent_test.py')
        result = analyzer._analyze_single_test_file(test_file)
        assert result is None
    
    @patch('builtins.open', mock_open(read_data=''))
    def test_analyze_single_test_file_empty(self, analyzer):
        """Test analysis of empty test file."""
        test_file = Path('empty_test.py')
        result = analyzer._analyze_single_test_file(test_file)
        assert result is None
    
    def test_analyze_test_coverage(self, analyzer):
        """Test test coverage analysis."""
        test_files = [
            Path('test_user.py'),
            Path('test_user_service.py'),
            Path('test_database.py')
        ]
        
        source_files = [
            Path('user.py'),
            Path('user_service.py'),
            Path('database.py'),
            Path('utils.py')  # No corresponding test
        ]
        
        result = analyzer._analyze_test_coverage(test_files, source_files)
        
        assert 'has_coverage_config' in result
        assert 'coverage_indicators' in result
        assert 'potentially_uncovered_files' in result
        assert 'test_to_source_mapping' in result
        assert 'estimated_coverage_percentage' in result
        
        # Should identify utils.py as potentially uncovered
        uncovered = result['potentially_uncovered_files']
        assert any('utils.py' in path for path in uncovered)
        
        # Should map test files to source files
        mapping = result['test_to_source_mapping']
        assert len(mapping) > 0
        
        # Coverage should be reasonable
        assert 0 <= result['estimated_coverage_percentage'] <= 1
    
    @patch('builtins.open', mock_open())
    def test_detect_test_frameworks_python(self, analyzer, sample_python_test_code):
        """Test Python test framework detection."""
        test_files = [Path('test_user.py')]
        
        with patch('builtins.open', mock_open(read_data=sample_python_test_code)):
            result = analyzer._detect_test_frameworks(test_files)
            
            assert 'detected_frameworks' in result
            assert 'framework_files' in result
            assert 'framework_confidence' in result
            
            frameworks = result['detected_frameworks']
            assert 'pytest' in frameworks or 'unittest' in frameworks
            
            # Should have confidence scores
            for framework in frameworks:
                assert framework in result['framework_confidence']
                assert 0 <= result['framework_confidence'][framework] <= 1
    
    @patch('builtins.open', mock_open())
    def test_detect_test_frameworks_javascript(self, analyzer, sample_javascript_test_code):
        """Test JavaScript test framework detection."""
        test_files = [Path('user.test.js')]
        
        with patch('builtins.open', mock_open(read_data=sample_javascript_test_code)):
            result = analyzer._detect_test_frameworks(test_files)
            
            frameworks = result['detected_frameworks']
            # Should detect framework based on describe/it patterns
            assert len(frameworks) > 0
    
    def test_calculate_test_metrics(self, analyzer):
        """Test test metrics calculation."""
        test_analysis = {
            'total_test_functions': 15,
            'total_assertions': 45,  # 3 assertions per test on average
            'test_classes': 5,
            'setup_teardown_count': 8
        }
        
        coverage_analysis = {
            'has_coverage_config': True,
            'estimated_coverage_percentage': 0.8
        }
        
        framework_analysis = {
            'detected_frameworks': ['pytest', 'unittest'],
            'framework_confidence': {'pytest': 0.7, 'unittest': 0.5}
        }
        
        test_file_count = 8
        source_file_count = 12
        
        result = analyzer._calculate_test_metrics(
            test_analysis, coverage_analysis, framework_analysis,
            test_file_count, source_file_count
        )
        
        assert 'coverage_score' in result
        assert 'test_to_source_ratio' in result
        assert 'estimated_success_rate' in result
        assert 'has_coverage_indicators' in result
        assert 'estimated_coverage' in result
        assert 'potentially_uncovered_files' in result
        
        # Check ranges
        assert 0 <= result['coverage_score'] <= 10
        assert 0 <= result['test_to_source_ratio'] <= 2  # Could be higher than 1
        assert 0.5 <= result['estimated_success_rate'] <= 1  # Minimum 50%
        assert result['has_coverage_indicators'] == True
        assert result['estimated_coverage'] == 0.8
    
    @patch('builtins.open', mock_open())
    def test_analyze_integration(self, analyzer, sample_python_test_code):
        """Test full analysis integration."""
        source_files = [
            Path('src/user.py'),
            Path('src/service.py'),
            Path('test_user.py'),
            Path('test_service.py')
        ]
        
        with patch('builtins.open', mock_open(read_data=sample_python_test_code)):
            result = analyzer.analyze(source_files)
            
            assert result is not None
            assert hasattr(result, 'coverage_score')
            assert hasattr(result, 'test_files_count')
            assert hasattr(result, 'test_to_source_ratio')
            assert hasattr(result, 'test_success_rate')
            assert hasattr(result, 'has_coverage_report')
            assert hasattr(result, 'coverage_percentage')
            assert hasattr(result, 'uncovered_files')
            
            # Check value ranges
            assert 0 <= result.coverage_score <= 10
            assert result.test_files_count >= 0
            assert 0 <= result.test_to_source_ratio <= 2
            assert 0.5 <= result.test_success_rate <= 1
            assert isinstance(result.has_coverage_report, bool)
            assert result.coverage_percentage is None or (0 <= result.coverage_percentage <= 1)
            assert isinstance(result.uncovered_files, list)
    
    def test_empty_source_files(self, analyzer):
        """Test analysis with empty source files."""
        result = analyzer.analyze([])
        
        assert result is not None
        assert result.coverage_score >= 0
        assert result.test_files_count == 0
        assert result.test_to_source_ratio == 0
    
    def test_no_test_files(self, analyzer):
        """Test analysis with no test files."""
        source_files = [Path('src/user.py'), Path('src/service.py')]
        result = analyzer.analyze(source_files)
        
        assert result is not None
        assert result.test_files_count == 0
        assert result.test_to_source_ratio == 0
        assert result.coverage_score < 5  # Should be low without tests
    
    def test_file_pattern_matching(self, analyzer):
        """Test file pattern matching for different languages."""
        patterns = analyzer.test_patterns['file_patterns']
        
        # Python patterns
        python_patterns = patterns['python']
        test_files = [
            'test_user.py', 'user_test.py', 'tests/test_module.py',
            'test/helper.py', 'conftest.py'
        ]
        
        for test_file in test_files:
            assert any(re.search(pattern, test_file) for pattern in python_patterns), \
                f"{test_file} should match Python test patterns"
        
        # JavaScript patterns
        js_patterns = patterns['javascript']
        js_test_files = [
            'user.test.js', 'user.spec.js', 'tests/user.js',
            '__tests__/user.js'
        ]
        
        for test_file in js_test_files:
            assert any(re.search(pattern, test_file) for pattern in js_patterns), \
                f"{test_file} should match JavaScript test patterns"
    
    def test_framework_pattern_matching(self, analyzer):
        """Test framework pattern matching."""
        frameworks = analyzer.framework_patterns
        
        # Python pytest patterns
        pytest_code = "import pytest\n@pytest.mark.parametrize"
        assert re.search(frameworks['python']['pytest'], pytest_code)
        
        # Python unittest patterns
        unittest_code = "import unittest\nclass TestCase(unittest.TestCase):"
        assert re.search(frameworks['python']['unittest'], unittest_code)
        
        # JavaScript jest patterns
        jest_code = "describe('test', () => { it('should work', () => {}); });"
        assert re.search(frameworks['javascript']['jest'], jest_code)
    
    def test_assertion_pattern_matching(self, analyzer):
        """Test assertion pattern matching."""
        patterns = analyzer.test_patterns['assertion_patterns']
        
        # Python assertions
        python_patterns = patterns['python']
        python_code = "assert x == 5\nself.assertEqual(a, b)\npytest.raises(ValueError)"
        
        total_assertions = 0
        for pattern in python_patterns:
            total_assertions += len(re.findall(pattern, python_code))
        
        assert total_assertions >= 3
        
        # JavaScript assertions
        js_patterns = patterns['javascript']
        js_code = "expect(result).toBe(5);\nassert.equal(a, b);\nresult.should.equal(expected);"
        
        total_js_assertions = 0
        for pattern in js_patterns:
            total_js_assertions += len(re.findall(pattern, js_code))
        
        assert total_js_assertions >= 2


if __name__ == '__main__':
    pytest.main([__file__])
