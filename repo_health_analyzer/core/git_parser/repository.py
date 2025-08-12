"""
Git repository parser for extracting repository information and commit history.

Handles parsing of git repositories to extract metadata, file structure,
and commit history for analysis.
"""

import os
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import defaultdict

import git
from git import Repo, InvalidGitRepositoryError

from ...models.report import RepositoryInfo


class GitRepositoryParser:
    """
    Parser for extracting information from git repositories.
    
    Provides methods to analyze repository structure, commit history,
    and file metadata for health analysis.
    """
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {repo_path}")
    
    def get_repository_info(self) -> RepositoryInfo:
        """
        Extract basic repository information.
        
        Returns:
            RepositoryInfo: Basic repository metadata
        """
        # Get repository statistics
        total_files, total_lines, languages = self._analyze_files()
        commit_count = len(list(self.repo.iter_commits()))
        contributors = len(set(commit.author.email for commit in self.repo.iter_commits()))
        
        # Calculate repository age
        try:
            first_commit = list(self.repo.iter_commits())[-1]
            age_days = (datetime.now(timezone.utc) - first_commit.committed_datetime).days
        except (IndexError, StopIteration):
            age_days = 0
        
        return RepositoryInfo(
            path=str(self.repo_path),
            name=self.repo_path.name,
            analyzed_at=datetime.now(timezone.utc),
            total_files=total_files,
            total_lines=total_lines,
            languages=languages,
            commit_count=commit_count,
            contributors=contributors,
            age_days=age_days
        )
    
    def get_source_files(self, include_patterns: List[str], exclude_patterns: List[str]) -> List[Path]:
        """
        Get list of source files matching include/exclude patterns.
        
        Args:
            include_patterns: File patterns to include (e.g., ['*.py', '*.js'])
            exclude_patterns: Directory patterns to exclude (e.g., ['*/node_modules/*'])
        
        Returns:
            List[Path]: List of source file paths
        """
        source_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip excluded directories
            root_path = Path(root)
            if self._should_exclude_directory(root_path, exclude_patterns):
                dirs.clear()  # Don't recurse into excluded directories
                continue
            
            for file in files:
                file_path = root_path / file
                if self._should_include_file(file_path, include_patterns, exclude_patterns):
                    source_files.append(file_path)
        
        return source_files
    
    def get_commit_history(self, max_commits: int = 1000) -> List[Dict[str, Any]]:
        """
        Extract commit history for sustainability analysis.
        
        Args:
            max_commits: Maximum number of commits to analyze
        
        Returns:
            List[Dict]: Commit history with metadata
        """
        commits = []
        
        try:
            for i, commit in enumerate(self.repo.iter_commits()):
                if i >= max_commits:
                    break
                
                # Calculate commit statistics
                stats = commit.stats.total
                
                commits.append({
                    'hash': commit.hexsha,
                    'author': commit.author.email,
                    'date': commit.committed_datetime,
                    'message': commit.message.strip(),
                    'files_changed': stats['files'],
                    'insertions': stats['insertions'],
                    'deletions': stats['deletions'],
                    'is_merge': len(commit.parents) > 1
                })
        
        except Exception as e:
            # Handle repositories with no commits or other git issues
            print(f"Warning: Could not parse commit history: {e}")
        
        return commits
    
    def get_file_content(self, file_path: Path) -> str:
        """
        Read file content safely.
        
        Args:
            file_path: Path to file
        
        Returns:
            str: File content or empty string if unreadable
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ""
    
    def get_file_history(self, file_path: Path, max_commits: int = 100) -> List[Dict[str, Any]]:
        """
        Get commit history for a specific file.
        
        Args:
            file_path: Path to file relative to repository root
            max_commits: Maximum commits to analyze
        
        Returns:
            List[Dict]: File-specific commit history
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
            commits = list(self.repo.iter_commits(paths=str(relative_path), max_count=max_commits))
            
            return [{
                'hash': commit.hexsha,
                'author': commit.author.email,
                'date': commit.committed_datetime,
                'message': commit.message.strip()
            } for commit in commits]
        
        except Exception:
            return []
    
    def _analyze_files(self) -> tuple[int, int, Dict[str, int]]:
        """
        Analyze repository files for statistics.
        
        Returns:
            Tuple of (total_files, total_lines, language_distribution)
        """
        total_files = 0
        total_lines = 0
        languages = defaultdict(int)
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git and other hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                total_files += 1
                
                # Count lines
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                except Exception:
                    continue
                
                # Detect language
                language = self._detect_language(file_path)
                if language:
                    languages[language] += lines
        
        return total_files, total_lines, dict(languages)
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            str: Programming language name
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.kt': 'Kotlin',
            '.swift': 'Swift',
            '.scala': 'Scala',
            '.sh': 'Shell',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
            '.vue': 'Vue',
            '.jsx': 'JSX',
            '.tsx': 'TSX',
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, '')
    
    def _should_include_file(self, file_path: Path, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
        """Check if file should be included in analysis."""
        # Check if file matches include patterns
        if include_patterns:
            import fnmatch
            if not any(fnmatch.fnmatch(str(file_path), pattern) or 
                      fnmatch.fnmatch(file_path.name, pattern.split('/')[-1] if '/' in pattern else pattern)
                      for pattern in include_patterns):
                return False
        
        # Check if file matches exclude patterns
        if exclude_patterns:
            import fnmatch
            if any(fnmatch.fnmatch(str(file_path), pattern) for pattern in exclude_patterns):
                return False
        
        # Skip binary files
        if self._is_binary_file(file_path):
            return False
        
        # Skip very large files (>10MB by default)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return False
        except OSError:
            return False
        
        return True
    
    def _should_exclude_directory(self, dir_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if directory should be excluded from analysis."""
        import fnmatch
        
        # Always exclude .git
        if dir_path.name == '.git':
            return True
        
        # Check exclude patterns
        return any(fnmatch.fnmatch(str(dir_path), pattern) for pattern in exclude_patterns)
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """
        Check if file is binary.
        
        Args:
            file_path: Path to file
        
        Returns:
            bool: True if file appears to be binary
        """
        try:
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and not mime_type.startswith('text/'):
                return True
            
            # Check for binary content in first 1024 bytes
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:  # Null bytes indicate binary
                    return True
            
            return False
        
        except Exception:
            return True  # Assume binary if we can't read it
