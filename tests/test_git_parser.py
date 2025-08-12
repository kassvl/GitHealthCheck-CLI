"""
Test suite for git repository parser.

Tests git repository parsing, file detection, and commit history extraction.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from repo_health_analyzer.core.git_parser.repository import GitRepositoryParser


class TestGitRepositoryParser:
    """Test cases for GitRepositoryParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def test_parser_invalid_repo(self):
        """Test parser raises error for invalid repository."""
        with pytest.raises(ValueError, match="Not a valid git repository"):
            GitRepositoryParser(self.temp_dir)
    
    def test_language_detection(self):
        """Test programming language detection from file extensions."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        # Create mock repo
        with patch('git.Repo') as mock_repo:
            mock_repo.return_value = Mock()
            parser = GitRepositoryParser(self.temp_dir)
            
            # Test language detection
            assert parser._detect_language(Path("test.py")) == "Python"
            assert parser._detect_language(Path("test.js")) == "JavaScript"
            assert parser._detect_language(Path("test.ts")) == "TypeScript"
            assert parser._detect_language(Path("test.java")) == "Java"
            assert parser._detect_language(Path("test.unknown")) == ""
    
    def test_binary_file_detection(self):
        """Test binary file detection."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        with patch('git.Repo') as mock_repo:
            mock_repo.return_value = Mock()
            parser = GitRepositoryParser(self.temp_dir)
            
            # Create test files
            text_file = self.temp_dir / "text.txt"
            text_file.write_text("This is a text file")
            
            binary_file = self.temp_dir / "binary.bin"
            binary_file.write_bytes(b"\x00\x01\x02\x03")
            
            assert not parser._is_binary_file(text_file)
            assert parser._is_binary_file(binary_file)
    
    def test_file_filtering(self):
        """Test file include/exclude pattern filtering."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        with patch('git.Repo') as mock_repo:
            mock_repo.return_value = Mock()
            parser = GitRepositoryParser(self.temp_dir)
            
            # Test include patterns
            assert parser._should_include_file(
                Path("test.py"), 
                ["*.py"], 
                []
            )
            
            assert not parser._should_include_file(
                Path("test.txt"), 
                ["*.py"], 
                []
            )
            
            # Test exclude patterns
            assert not parser._should_include_file(
                Path("node_modules/test.js"), 
                ["*.js"], 
                ["*/node_modules/*"]
            )
    
    def test_directory_exclusion(self):
        """Test directory exclusion logic."""
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        
        with patch('git.Repo') as mock_repo:
            mock_repo.return_value = Mock()
            parser = GitRepositoryParser(self.temp_dir)
            
            # Test .git exclusion
            assert parser._should_exclude_directory(Path(".git"), [])
            
            # Test pattern exclusion
            assert parser._should_exclude_directory(
                Path("node_modules"), 
                ["*/node_modules/*"]
            )
            
            assert not parser._should_exclude_directory(
                Path("src"), 
                ["*/node_modules/*"]
            )
