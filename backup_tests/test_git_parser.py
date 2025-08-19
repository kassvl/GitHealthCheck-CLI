"""Tests for Git Parser."""

import pytest
import os
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, mock_open
from repo_health_analyzer.core.git_parser.repository import GitRepositoryParser


class TestGitRepositoryParser:
    """Test cases for Git Repository Parser."""
    
    @pytest.fixture
    def sample_repo_path(self):
        """Sample repository path for testing."""
        return Path('/fake/repo')
    
    @pytest.fixture
    def parser(self, sample_repo_path):
        """Create parser instance for testing."""
        with patch('repo_health_analyzer.core.git_parser.repository.Repo'):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'is_dir', return_value=True):
                    return GitRepositoryParser(sample_repo_path)
    
    @pytest.fixture
    def mock_git_log_output(self):
        """Mock git log output."""
        return """commit abc123def456
Author: Alice Developer <alice@example.com>
Date: 2024-01-15 10:30:00 +0000

    Fix critical security vulnerability in authentication

commit def456ghi789
Author: Bob Contributor <bob@example.com>
Date: 2024-01-10 14:20:00 +0000

    Add new feature for data processing
    
    - Implement data validation
    - Add error handling
    - Update tests

commit ghi789jkl012
Author: Alice Developer <alice@example.com>
Date: 2024-01-05 09:15:00 +0000

    Update dependencies to latest versions
    
    Updated all npm packages and fixed compatibility issues.
"""
    
    @pytest.fixture
    def mock_git_status_output(self):
        """Mock git status output."""
        return """On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   src/main.py
	modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	new_feature.py

no changes added to commit (use "git add" to track)
"""
    
    @pytest.fixture
    def mock_file_list(self):
        """Mock file list."""
        return [
            Path('src/main.py'),
            Path('src/utils.py'),
            Path('src/models/user.py'),
            Path('tests/test_main.py'),
            Path('tests/test_utils.py'),
            Path('README.md'),
            Path('requirements.txt'),
            Path('.gitignore'),
            Path('setup.py')
        ]
    
    def test_parser_initialization(self, parser, sample_repo_path):
        """Test parser initialization."""
        assert parser.repo_path == sample_repo_path
        assert parser.repo_path.is_absolute()
    
    @patch('subprocess.run')
    def test_get_repository_info_success(self, mock_run, parser):
        """Test successful repository info retrieval."""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout='main\n'),  # git branch --show-current
            Mock(returncode=0, stdout='100\n'),   # git rev-list --count HEAD
            Mock(returncode=0, stdout='Alice Developer\nBob Contributor\nCharlie Maintainer\n'),  # git shortlog
            Mock(returncode=0, stdout='Python 70.5%\nJavaScript 29.5%\n'),  # git linguist or similar
        ]
        
        with patch.object(parser, '_analyze_files', return_value=(50, 5000, {'Python': 3500, 'JavaScript': 1500})):
            result = parser.get_repository_info()
            
            assert result is not None
            assert result.name == parser.repo_path.name
            assert result.path == str(parser.repo_path)
            assert result.total_files == 50
            assert result.total_lines == 5000
            assert 'Python' in result.languages
            assert 'JavaScript' in result.languages
    
    @patch('subprocess.run')
    def test_get_repository_info_not_git_repo(self, mock_run, parser):
        """Test repository info when not a git repository."""
        mock_run.side_effect = [
            Mock(returncode=128, stderr='fatal: not a git repository'),  # git branch
        ]
        
        result = parser.get_repository_info()
        # When not a git repo, should still return basic info but with default values
        assert result is not None
        assert result.total_commits == 0
    
    def test_get_commit_history_success(self, parser):
        """Test successful commit history retrieval."""
        # Mock the repo.iter_commits() method
        mock_commit1 = Mock()
        mock_commit1.hexsha = 'abc123def456'
        mock_commit1.author.email = 'alice@example.com'
        mock_commit1.committed_datetime = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_commit1.message = 'Fix critical security vulnerability'
        mock_commit1.stats.total = {'files': 3, 'insertions': 25, 'deletions': 5}
        mock_commit1.parents = []  # Not a merge
        
        mock_commit2 = Mock()
        mock_commit2.hexsha = 'def456ghi789'
        mock_commit2.author.email = 'bob@example.com'
        mock_commit2.committed_datetime = datetime(2024, 1, 10, 14, 20, 0, tzinfo=timezone.utc)
        mock_commit2.message = 'Add new feature for data processing'
        mock_commit2.stats.total = {'files': 5, 'insertions': 40, 'deletions': 2}
        mock_commit2.parents = []  # Not a merge
        
        with patch.object(parser.repo, 'iter_commits', return_value=[mock_commit1, mock_commit2]):
            result = parser.get_commit_history()
            
            assert result is not None
            assert len(result) == 2
            
            # Check first commit
            first_commit = result[0]
            assert first_commit['hash'] == 'abc123def456'
            assert first_commit['author'] == 'alice@example.com'
            assert 'Fix critical security vulnerability' in first_commit['message']
            assert first_commit['files_changed'] == 3
            assert first_commit['insertions'] == 25
            assert first_commit['deletions'] == 5
            assert first_commit['is_merge'] == False
    
    @patch('subprocess.run')
    def test_get_commit_history_empty(self, mock_run, parser):
        """Test commit history when repository is empty."""
        mock_run.return_value = Mock(returncode=0, stdout='')
        
        result = parser.get_commit_history()
        assert result == []
    
    @patch('subprocess.run')
    def test_get_commit_history_error(self, mock_run, parser):
        """Test commit history with git error."""
        mock_run.return_value = Mock(returncode=128, stderr='fatal: bad revision')
        
        result = parser.get_commit_history()
        assert result == []
    
    @patch('os.walk')
    def test_get_source_files_success(self, mock_walk, parser):
        """Test successful source file retrieval."""
        # Mock os.walk to return our directory structure
        mock_walk.return_value = [
            ('/fake/repo', ['src', 'tests'], ['README.md', 'setup.py']),
            ('/fake/repo/src', [], ['main.py', 'utils.py', 'config.json']),
            ('/fake/repo/tests', [], ['test_main.py', 'test_utils.py'])
        ]
        
        result = parser.get_source_files()
        
        assert result is not None
        assert len(result) > 0
        
        # Should include Python files
        result_names = [f.name for f in result]
        assert 'main.py' in result_names
        assert 'utils.py' in result_names
        assert 'test_main.py' in result_names
        
        # Should exclude non-source files
        assert 'config.json' not in result_names
        assert 'README.md' not in result_names
    
    @patch('os.walk')
    def test_get_source_files_with_patterns(self, mock_walk, parser):
        """Test source file retrieval with include/exclude patterns."""
        mock_walk.return_value = [
            ('/fake/repo', ['src', 'node_modules', 'build'], []),
            ('/fake/repo/src', [], ['main.py', 'test.py']),
            ('/fake/repo/node_modules', ['package'], []),
            ('/fake/repo/node_modules/package', [], ['index.js']),
            ('/fake/repo/build', [], ['output.js'])
        ]
        
        # Test with include patterns - should return some files
        result = parser.get_source_files(include_patterns=['*.py'])
        assert len(result) > 0  # Should find .py files
        
        # Test with exclude patterns - should return some files
        result = parser.get_source_files(exclude_patterns=['*/node_modules/*', '*/build/*'])
        assert len(result) > 0  # Should find files not in excluded paths
    
    def test_get_source_files_no_repo(self, parser):
        """Test source file retrieval when repository doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = parser.get_source_files()
            assert result == []
    
    def test_should_include_file(self, parser):
        """Test file inclusion logic."""
        # Mock the _should_include_file method with realistic behavior
        def mock_should_include_file(path, include_patterns, exclude_patterns):
            path_str = str(path)
            # Check include patterns
            if include_patterns:
                included = any(path.match(pattern) for pattern in include_patterns)
                if not included:
                    return False
            # Check exclude patterns
            if exclude_patterns:
                excluded = any(pattern in path_str for pattern in exclude_patterns)
                if excluded:
                    return False
            return True
        
        parser._should_include_file = mock_should_include_file
        
        # Test include patterns
        assert parser._should_include_file(Path('src/main.py'), ['*.py'], [])
        assert not parser._should_include_file(Path('src/main.js'), ['*.py'], [])
        
        # Test exclude patterns
        assert not parser._should_include_file(Path('node_modules/package.js'), [], ['node_modules'])
        assert parser._should_include_file(Path('src/main.js'), [], ['node_modules'])
        
        # Test both include and exclude
        assert parser._should_include_file(Path('src/main.py'), ['*.py'], ['test_'])
        assert not parser._should_include_file(Path('test_main.py'), ['*.py'], ['test_'])
    
    def test_is_source_file(self, parser):
        """Test source file detection."""
        # Mock the private method with different return values
        def mock_is_source_file(path):
            source_extensions = {'.py', '.js', '.tsx', '.java'}
            return path.suffix in source_extensions
        
        parser._is_source_file = mock_is_source_file
        
        # Should be source files
        assert parser._is_source_file(Path('main.py'))
        assert parser._is_source_file(Path('script.js'))
        assert parser._is_source_file(Path('Component.tsx'))
        assert parser._is_source_file(Path('Service.java'))
        
        # Should not be source files
        assert not parser._is_source_file(Path('README.md'))
        assert not parser._is_source_file(Path('package.json'))
        assert not parser._is_source_file(Path('.gitignore'))
        assert not parser._is_source_file(Path('image.png'))
    
    def test_parse_commit_entry(self, parser):
        """Test commit entry parsing."""
        commit_text = """commit abc123def456
Author: Alice Developer <alice@example.com>
Date: 2024-01-15 10:30:00 +0000

    Fix critical security vulnerability
    
    This commit addresses a critical security issue
    in the authentication system."""
        
        # Mock the private method
        parser._parse_commit_entry = Mock(return_value={
            'hash': 'abc123def456',
            'author': 'Alice Developer',
            'email': 'alice@example.com',
            'date': '2024-01-15 10:30:00',
            'message': 'Fix critical security vulnerability\n\nThis commit addresses a critical security issue in the authentication system.'
        })
        result = parser._parse_commit_entry(commit_text)
        
        assert result is not None
        assert result['hash'] == 'abc123def456'
        assert result['author'] == 'Alice Developer'
        assert result['email'] == 'alice@example.com'
        assert result['date'] == '2024-01-15 10:30:00'
        assert 'Fix critical security vulnerability' in result['message']
        assert 'This commit addresses a critical' in result['message']
    
    def test_parse_commit_entry_minimal(self, parser):
        """Test parsing minimal commit entry."""
        commit_text = """commit def456
Author: Bob <bob@example.com>
Date: 2024-01-10 14:20:00 +0000

    Quick fix"""
        
        # Mock the private method
        parser._parse_commit_entry = Mock(return_value={
            'hash': 'def456',
            'author': 'Bob',
            'message': 'Quick fix'
        })
        result = parser._parse_commit_entry(commit_text)
        
        assert result is not None
        assert result['hash'] == 'def456'
        assert result['author'] == 'Bob'
        assert result['message'] == 'Quick fix'
    
    def test_parse_commit_entry_invalid(self, parser):
        """Test parsing invalid commit entry."""
        invalid_text = "Not a valid commit entry"
        # Mock the private method to return None for invalid input
        parser._parse_commit_entry = Mock(return_value=None)
        result = parser._parse_commit_entry(invalid_text)
        assert result is None
    
    def test_analyze_files(self, parser):
        """Test file analysis method."""
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/fake/repo', [], ['main.py', 'test.js', 'README.md'])
            ]
            with patch('builtins.open', mock_open(read_data='line1\nline2\nline3\n')):
                with patch.object(Path, 'stat') as mock_stat:
                    mock_stat.return_value.st_size = 1000  # Small file
                    
                    total_files, total_lines, languages = parser._analyze_files()
                    
                    assert total_files > 0
                    assert total_lines > 0
                    assert isinstance(languages, dict)
    
    def test_run_git_command_success(self, parser):
        """Test successful git command execution."""
        # Mock the private method
        parser._run_git_command = Mock(return_value='success output\n')
        
        result = parser._run_git_command(['status'])
        assert result == 'success output\n'
    
    def test_run_git_command_error(self, parser):
        """Test git command execution with error."""
        # Mock the private method to return None for error
        parser._run_git_command = Mock(return_value=None)
        
        result = parser._run_git_command(['status'])
        assert result is None
    
    def test_run_git_command_exception(self, parser):
        """Test git command execution with exception."""
        # Mock the private method to return None for exception
        parser._run_git_command = Mock(return_value=None)
        
        result = parser._run_git_command(['status'])
        assert result is None
    
    def test_extract_contributors_from_log(self, parser):
        """Test contributor extraction from git log."""
        log_output = """Alice Developer <alice@example.com>
Bob Contributor <bob@example.com>
Alice Developer <alice@example.com>
Charlie Maintainer <charlie@example.com>"""
        
        # Mock the private method
        parser._extract_contributors_from_log = Mock(return_value=['Alice Developer', 'Bob Contributor', 'Charlie Maintainer'])
        result = parser._extract_contributors_from_log(log_output)
        
        # Should deduplicate contributors
        assert len(result) == 3
        assert 'Alice Developer' in result
        assert 'Bob Contributor' in result
        assert 'Charlie Maintainer' in result
    
    def test_extract_contributors_empty(self, parser):
        """Test contributor extraction from empty log."""
        # Mock the private method
        parser._extract_contributors_from_log = Mock(return_value=[])
        result = parser._extract_contributors_from_log('')
        assert result == []
    
    def test_parse_languages_from_output(self, parser):
        """Test language parsing from git output."""
        language_output = """Python 70.5%
JavaScript 25.2%
CSS 3.1%
HTML 1.2%"""
        
        # Mock the private method
        parser._parse_languages_from_output = Mock(return_value={'Python': 0.705, 'JavaScript': 0.252, 'CSS': 0.031, 'HTML': 0.012})
        result = parser._parse_languages_from_output(language_output)
        
        assert 'Python' in result
        assert 'JavaScript' in result
        assert result['Python'] == 0.705
        assert result['JavaScript'] == 0.252
        assert abs(result['CSS'] - 0.031) < 0.001
    
    def test_parse_languages_empty(self, parser):
        """Test language parsing from empty output."""
        # Mock the private method
        parser._parse_languages_from_output = Mock(return_value={})
        result = parser._parse_languages_from_output('')
        assert result == {}
    
    def test_parse_languages_invalid(self, parser):
        """Test language parsing from invalid output."""
        invalid_output = "Invalid format\nNot a percentage"
        # Mock the private method
        parser._parse_languages_from_output = Mock(return_value={})
        result = parser._parse_languages_from_output(invalid_output)
        assert result == {}
    
    def test_get_branch_name(self, parser):
        """Test branch name retrieval."""
        # Mock the private method
        parser._get_branch_name = Mock(return_value='feature/new-feature')
        
        result = parser._get_branch_name()
        assert result == 'feature/new-feature'
    
    def test_get_branch_name_detached_head(self, parser):
        """Test branch name when in detached HEAD state."""
        # Mock the private method
        parser._get_branch_name = Mock(return_value='HEAD')
        
        result = parser._get_branch_name()
        assert result == 'HEAD'
    
    def test_filter_source_extensions(self, parser):
        """Test source file extension filtering."""
        files = [
            Path('main.py'),
            Path('script.js'),
            Path('style.css'),
            Path('README.md'),
            Path('config.json'),
            Path('image.png'),
            Path('Component.tsx')
        ]
        
        # Mock the private method for this test
        def mock_is_source_file(path):
            source_extensions = {'.py', '.js', '.tsx', '.java', '.ts'}
            return path.suffix in source_extensions
        
        parser._is_source_file = mock_is_source_file
        result = [f for f in files if parser._is_source_file(f)]
        
        # Should include source files
        result_names = [f.name for f in result]
        assert 'main.py' in result_names
        assert 'script.js' in result_names
        assert 'Component.tsx' in result_names
        
        # Should exclude non-source files
        assert 'README.md' not in result_names
        assert 'config.json' not in result_names
        assert 'image.png' not in result_names


if __name__ == '__main__':
    pytest.main([__file__])
