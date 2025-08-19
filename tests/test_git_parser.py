"""Tests for Git Parser."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from repo_health_analyzer.core.git_parser.repository import GitRepositoryParser


@patch('repo_health_analyzer.core.git_parser.repository.Repo')
@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'is_dir', return_value=True)
class TestGitRepositoryParser:
    """Test cases for Git Repository Parser."""
    
    @pytest.fixture
    def sample_repo_path(self):
        """Sample repository path for testing."""
        return Path('/fake/repo')
    
    @pytest.fixture
    def parser(self, sample_repo_path):
        """Create parser instance for testing."""
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
        
        with patch.object(parser, '_get_total_files', return_value=50):
            with patch.object(parser, '_get_total_lines', return_value=5000):
                result = parser.get_repository_info()
                
                assert result is not None
                assert result.name == parser.repo_path.name
                assert result.path == str(parser.repo_path)
                assert result.branch == 'main'
                assert result.total_commits == 100
                assert len(result.contributors) == 3
                assert 'Alice Developer' in result.contributors
                assert result.total_files == 50
                assert result.total_lines == 5000
    
    @patch('subprocess.run')
    def test_get_repository_info_not_git_repo(self, mock_run, parser):
        """Test repository info when not a git repository."""
        mock_run.side_effect = [
            Mock(returncode=128, stderr='fatal: not a git repository'),  # git branch
        ]
        
        result = parser.get_repository_info()
        assert result is None
    
    @patch('subprocess.run')
    def test_get_commit_history_success(self, mock_run, parser, mock_git_log_output):
        """Test successful commit history retrieval."""
        mock_run.return_value = Mock(returncode=0, stdout=mock_git_log_output)
        
        result = parser.get_commit_history(limit=100)
        
        assert result is not None
        assert len(result) == 3
        
        # Check first commit
        first_commit = result[0]
        assert first_commit['hash'] == 'abc123def456'
        assert first_commit['author'] == 'Alice Developer'
        assert first_commit['email'] == 'alice@example.com'
        assert 'Fix critical security vulnerability' in first_commit['message']
        assert '2024-01-15' in first_commit['date']
        
        # Check second commit (multiline message)
        second_commit = result[1]
        assert second_commit['hash'] == 'def456ghi789'
        assert second_commit['author'] == 'Bob Contributor'
        assert 'Add new feature for data processing' in second_commit['message']
        assert '- Implement data validation' in second_commit['message']
    
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
    
    @patch('pathlib.Path.rglob')
    def test_get_source_files_success(self, mock_rglob, parser, mock_file_list):
        """Test successful source file retrieval."""
        mock_rglob.return_value = mock_file_list
        
        with patch.object(Path, 'is_file', return_value=True):
            with patch.object(Path, 'exists', return_value=True):
                result = parser.get_source_files()
                
                assert result is not None
                assert len(result) > 0
                
                # Should include Python files
                py_files = [f for f in result if f.suffix == '.py']
                assert len(py_files) > 0
                
                # Should exclude certain files
                result_names = [f.name for f in result]
                assert '.gitignore' not in result_names  # Should be filtered
    
    @patch('pathlib.Path.rglob')
    def test_get_source_files_with_patterns(self, mock_rglob, parser):
        """Test source file retrieval with include/exclude patterns."""
        mock_files = [
            Path('src/main.py'),
            Path('src/test.py'),
            Path('node_modules/package/index.js'),
            Path('build/output.js'),
            Path('docs/readme.md')
        ]
        mock_rglob.return_value = mock_files
        
        with patch.object(Path, 'is_file', return_value=True):
            with patch.object(Path, 'exists', return_value=True):
                # Test with include patterns
                result = parser.get_source_files(include_patterns=['*.py'])
                py_files = [f for f in result if f.suffix == '.py']
                assert len(py_files) > 0
                
                # Test with exclude patterns
                result = parser.get_source_files(exclude_patterns=['node_modules/*', 'build/*'])
                result_paths = [str(f) for f in result]
                assert not any('node_modules' in path for path in result_paths)
                assert not any('build' in path for path in result_paths)
    
    def test_get_source_files_no_repo(self, parser):
        """Test source file retrieval when repository doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = parser.get_source_files()
            assert result == []
    
    def test_should_include_file(self, parser):
        """Test file inclusion logic."""
        # Test include patterns
        assert parser._should_include_file(Path('src/main.py'), ['*.py'], [])
        assert not parser._should_include_file(Path('src/main.js'), ['*.py'], [])
        
        # Test exclude patterns
        assert not parser._should_include_file(Path('node_modules/package.js'), [], ['node_modules/*'])
        assert parser._should_include_file(Path('src/main.js'), [], ['node_modules/*'])
        
        # Test both include and exclude
        assert parser._should_include_file(Path('src/main.py'), ['*.py'], ['test_*'])
        assert not parser._should_include_file(Path('test_main.py'), ['*.py'], ['test_*'])
    
    def test_is_source_file(self, parser):
        """Test source file detection."""
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
        
        result = parser._parse_commit_entry(commit_text)
        
        assert result is not None
        assert result['hash'] == 'def456'
        assert result['author'] == 'Bob'
        assert result['message'] == 'Quick fix'
    
    def test_parse_commit_entry_invalid(self, parser):
        """Test parsing invalid commit entry."""
        invalid_text = "Not a valid commit entry"
        result = parser._parse_commit_entry(invalid_text)
        assert result is None
    
    @patch('subprocess.run')
    def test_get_total_files(self, mock_run, parser):
        """Test total files count."""
        mock_run.return_value = Mock(returncode=0, stdout='150\n')
        
        result = parser._get_total_files()
        assert result == 150
    
    @patch('subprocess.run')
    def test_get_total_files_error(self, mock_run, parser):
        """Test total files count with error."""
        mock_run.return_value = Mock(returncode=1, stderr='error')
        
        result = parser._get_total_files()
        assert result == 0
    
    @patch('subprocess.run')
    def test_get_total_lines(self, mock_run, parser):
        """Test total lines count."""
        mock_run.return_value = Mock(returncode=0, stdout='5000\n')
        
        result = parser._get_total_lines()
        assert result == 5000
    
    @patch('subprocess.run')
    def test_get_total_lines_error(self, mock_run, parser):
        """Test total lines count with error."""
        mock_run.return_value = Mock(returncode=1, stderr='error')
        
        result = parser._get_total_lines()
        assert result == 0
    
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run, parser):
        """Test successful git command execution."""
        mock_run.return_value = Mock(returncode=0, stdout='success output\n')
        
        result = parser._run_git_command(['status'])
        assert result == 'success output\n'
    
    @patch('subprocess.run')
    def test_run_git_command_error(self, mock_run, parser):
        """Test git command execution with error."""
        mock_run.return_value = Mock(returncode=128, stderr='fatal: not a git repository')
        
        result = parser._run_git_command(['status'])
        assert result is None
    
    @patch('subprocess.run')
    def test_run_git_command_exception(self, mock_run, parser):
        """Test git command execution with exception."""
        mock_run.side_effect = Exception('Command failed')
        
        result = parser._run_git_command(['status'])
        assert result is None
    
    def test_extract_contributors_from_log(self, parser):
        """Test contributor extraction from git log."""
        log_output = """Alice Developer <alice@example.com>
Bob Contributor <bob@example.com>
Alice Developer <alice@example.com>
Charlie Maintainer <charlie@example.com>"""
        
        result = parser._extract_contributors_from_log(log_output)
        
        # Should deduplicate contributors
        assert len(result) == 3
        assert 'Alice Developer' in result
        assert 'Bob Contributor' in result
        assert 'Charlie Maintainer' in result
    
    def test_extract_contributors_empty(self, parser):
        """Test contributor extraction from empty log."""
        result = parser._extract_contributors_from_log('')
        assert result == []
    
    def test_parse_languages_from_output(self, parser):
        """Test language parsing from git output."""
        language_output = """Python 70.5%
JavaScript 25.2%
CSS 3.1%
HTML 1.2%"""
        
        result = parser._parse_languages_from_output(language_output)
        
        assert 'Python' in result
        assert 'JavaScript' in result
        assert result['Python'] == 0.705
        assert result['JavaScript'] == 0.252
        assert abs(result['CSS'] - 0.031) < 0.001
    
    def test_parse_languages_empty(self, parser):
        """Test language parsing from empty output."""
        result = parser._parse_languages_from_output('')
        assert result == {}
    
    def test_parse_languages_invalid(self, parser):
        """Test language parsing from invalid output."""
        invalid_output = "Invalid format\nNot a percentage"
        result = parser._parse_languages_from_output(invalid_output)
        assert result == {}
    
    @patch('subprocess.run')
    def test_get_branch_name(self, mock_run, parser):
        """Test branch name retrieval."""
        mock_run.return_value = Mock(returncode=0, stdout='feature/new-feature\n')
        
        result = parser._get_branch_name()
        assert result == 'feature/new-feature'
    
    @patch('subprocess.run')
    def test_get_branch_name_detached_head(self, mock_run, parser):
        """Test branch name when in detached HEAD state."""
        mock_run.return_value = Mock(returncode=1, stderr='fatal: ref HEAD is not a symbolic ref')
        
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
