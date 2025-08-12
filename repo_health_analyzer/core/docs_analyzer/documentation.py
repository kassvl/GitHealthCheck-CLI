"""
Documentation quality analyzer.

Evaluates documentation completeness, quality, and accessibility.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any

from ...models.report import DocumentationMetrics, AnalysisConfig


class DocumentationAnalyzer:
    """
    Analyzer for documentation quality and completeness.
    
    Evaluates README quality, docstring coverage, API documentation,
    and presence of standard documentation files.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
    
    def analyze(self, repo_path: Path, source_files: List[Path]) -> DocumentationMetrics:
        """
        Analyze documentation quality and completeness.
        
        Args:
            repo_path: Repository root path
            source_files: List of source file paths
        
        Returns:
            DocumentationMetrics: Documentation quality metrics
        """
        # Analyze README quality
        readme_quality = self._analyze_readme_quality(repo_path)
        
        # Calculate docstring coverage
        docstring_coverage = self._calculate_docstring_coverage(source_files)
        
        # Estimate API documentation coverage
        api_doc_coverage = self._estimate_api_doc_coverage(repo_path, source_files)
        
        # Check for standard documentation files
        has_changelog = self._has_changelog(repo_path)
        has_contributing_guide = self._has_contributing_guide(repo_path)
        
        # Count documentation files
        doc_files_count = self._count_doc_files(repo_path)
        
        # Calculate overall documentation score
        score = self._calculate_documentation_score(
            readme_quality, docstring_coverage, api_doc_coverage,
            has_changelog, has_contributing_guide, doc_files_count
        )
        
        return DocumentationMetrics(
            score=round(score, 1),
            readme_quality=round(readme_quality, 2),
            docstring_coverage=round(docstring_coverage, 3),
            api_doc_coverage=round(api_doc_coverage, 3),
            has_changelog=has_changelog,
            has_contributing_guide=has_contributing_guide,
            doc_files_count=doc_files_count
        )
    
    def _analyze_readme_quality(self, repo_path: Path) -> float:
        """
        Analyze README file quality.
        
        Args:
            repo_path: Repository root path
        
        Returns:
            float: README quality score (0-10)
        """
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
        readme_content = ""
        
        for readme_file in readme_files:
            readme_path = repo_path / readme_file
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        readme_content = f.read()
                    break
                except Exception:
                    continue
        
        if not readme_content:
            return 0.0
        
        score = 0.0
        
        # Length check (reasonable length indicates effort)
        if len(readme_content) > 200:
            score += 2.0
        if len(readme_content) > 1000:
            score += 1.0
        
        # Check for key sections
        content_lower = readme_content.lower()
        
        sections_to_check = [
            ('installation', ['install', 'setup', 'getting started']),
            ('usage', ['usage', 'example', 'how to use']),
            ('description', ['description', 'about', 'what is']),
            ('api', ['api', 'reference', 'documentation']),
            ('contributing', ['contribut', 'development', 'pull request']),
            ('license', ['license', 'licensing']),
        ]
        
        for section_name, keywords in sections_to_check:
            if any(keyword in content_lower for keyword in keywords):
                score += 1.0
        
        # Check for code examples
        if '```' in readme_content or '    ' in readme_content:  # Code blocks
            score += 1.0
        
        # Check for badges/shields (indicates active maintenance)
        if re.search(r'!\[.*\]\(.*badge.*\)', readme_content):
            score += 0.5
        
        return min(10.0, score)
    
    def _calculate_docstring_coverage(self, source_files: List[Path]) -> float:
        """
        Calculate docstring coverage for Python files.
        
        Args:
            source_files: List of source file paths
        
        Returns:
            float: Docstring coverage ratio (0-1)
        """
        total_functions = 0
        documented_functions = 0
        
        for file_path in source_files:
            if file_path.suffix == '.py':
                file_coverage = self._analyze_python_docstrings(file_path)
                total_functions += file_coverage['total']
                documented_functions += file_coverage['documented']
        
        if total_functions == 0:
            return 0.0
        
        return documented_functions / total_functions
    
    def _analyze_python_docstrings(self, file_path: Path) -> Dict[str, int]:
        """Analyze docstring coverage in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            total = 0
            documented = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total += 1
                    
                    # Check if function/class has docstring
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        documented += 1
            
            return {'total': total, 'documented': documented}
        
        except Exception:
            return {'total': 0, 'documented': 0}
    
    def _estimate_api_doc_coverage(self, repo_path: Path, source_files: List[Path]) -> float:
        """
        Estimate API documentation coverage.
        
        Args:
            repo_path: Repository root path
            source_files: List of source file paths
        
        Returns:
            float: API documentation coverage estimate (0-1)
        """
        # Look for documentation directories
        doc_dirs = ['docs', 'doc', 'documentation', 'api-docs']
        has_doc_dir = any((repo_path / doc_dir).exists() for doc_dir in doc_dirs)
        
        if has_doc_dir:
            return 0.8  # Assume good coverage if dedicated docs exist
        
        # Count public functions/classes that might need documentation
        public_apis = 0
        for file_path in source_files:
            if file_path.suffix == '.py':
                public_apis += self._count_public_apis(file_path)
        
        # If no public APIs found, assume good coverage
        if public_apis == 0:
            return 1.0
        
        # Estimate based on docstring coverage
        docstring_coverage = self._calculate_docstring_coverage(source_files)
        return docstring_coverage * 0.8  # Slightly lower than docstring coverage
    
    def _count_public_apis(self, file_path: Path) -> int:
        """Count public APIs (functions/classes) in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Count non-private functions
                    if not node.name.startswith('_'):
                        count += 1
                
                elif isinstance(node, ast.ClassDef):
                    # Count non-private classes
                    if not node.name.startswith('_'):
                        count += 1
            
            return count
        
        except Exception:
            return 0
    
    def _has_changelog(self, repo_path: Path) -> bool:
        """Check if repository has a changelog."""
        changelog_files = [
            'CHANGELOG.md', 'CHANGELOG.rst', 'CHANGELOG.txt', 'CHANGELOG',
            'HISTORY.md', 'HISTORY.rst', 'HISTORY.txt', 'HISTORY',
            'CHANGES.md', 'CHANGES.rst', 'CHANGES.txt', 'CHANGES'
        ]
        
        return any((repo_path / changelog).exists() for changelog in changelog_files)
    
    def _has_contributing_guide(self, repo_path: Path) -> bool:
        """Check if repository has a contributing guide."""
        contributing_files = [
            'CONTRIBUTING.md', 'CONTRIBUTING.rst', 'CONTRIBUTING.txt', 'CONTRIBUTING',
            '.github/CONTRIBUTING.md',
            'docs/CONTRIBUTING.md',
            'doc/CONTRIBUTING.md'
        ]
        
        return any((repo_path / contrib).exists() for contrib in contributing_files)
    
    def _count_doc_files(self, repo_path: Path) -> int:
        """Count documentation files in the repository."""
        doc_extensions = {'.md', '.rst', '.txt', '.adoc', '.asciidoc'}
        doc_count = 0
        
        # Check root directory for documentation files
        for file_path in repo_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in doc_extensions:
                doc_count += 1
        
        # Check docs directories
        doc_dirs = ['docs', 'doc', 'documentation']
        for doc_dir in doc_dirs:
            doc_path = repo_path / doc_dir
            if doc_path.exists() and doc_path.is_dir():
                for file_path in doc_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in doc_extensions:
                        doc_count += 1
        
        return doc_count
    
    def _calculate_documentation_score(
        self, readme_quality: float, docstring_coverage: float, 
        api_doc_coverage: float, has_changelog: bool, 
        has_contributing: bool, doc_files_count: int
    ) -> float:
        """Calculate overall documentation score."""
        
        # Weighted scoring
        score = 0.0
        
        # README quality (30% weight)
        score += (readme_quality / 10) * 3
        
        # Docstring coverage (25% weight)
        score += docstring_coverage * 2.5
        
        # API documentation (20% weight)
        score += api_doc_coverage * 2
        
        # Standard files (15% weight)
        if has_changelog:
            score += 0.75
        if has_contributing:
            score += 0.75
        
        # Documentation files count (10% weight)
        doc_score = min(1.0, doc_files_count / 5)  # 5+ doc files = full points
        score += doc_score * 1
        
        return min(10.0, score)
