"""
Interface definitions for analyzer components.

Defines abstract base classes and protocols for consistent analyzer implementation.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any, Protocol, runtime_checkable


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Protocol for all analyzer components."""
    
    def analyze(self, *args, **kwargs) -> Any:
        """Perform analysis and return results."""
        ...


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.
    
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> Any:
        """
        Perform analysis and return metrics.
        
        Must be implemented by all concrete analyzer classes.
        """
        pass
    
    def _validate_input(self, source_files: List[Path]) -> None:
        """Validate input parameters common to all analyzers."""
        if not isinstance(source_files, list):
            raise TypeError("source_files must be a list")
        
        for file_path in source_files:
            if not isinstance(file_path, Path):
                raise TypeError("All source files must be Path objects")
            if not file_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is supported for analysis."""
        supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
        return file_path.suffix.lower() in supported_extensions


class FileAnalyzerMixin:
    """
    Mixin for analyzers that process individual files.
    
    Provides common file processing utilities.
    """
    
    def _read_file_safely(self, file_path: Path) -> str:
        """Read file content with error handling."""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='latin-1')
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")
            return ""
    
    def _get_file_lines(self, file_path: Path) -> List[str]:
        """Get file lines with error handling."""
        content = self._read_file_safely(file_path)
        return content.splitlines() if content else []


class RepositoryAnalyzerInterface(ABC):
    """Interface for repository-level analyzers."""
    
    @abstractmethod
    def analyze_repository(self, repo_path: Path) -> Any:
        """Analyze the entire repository."""
        pass


class MetricsCalculatorInterface(ABC):
    """Interface for metrics calculation components."""
    
    @abstractmethod
    def calculate_score(self, *args, **kwargs) -> float:
        """Calculate a numeric score."""
        pass
    
    @abstractmethod
    def generate_recommendations(self, *args, **kwargs) -> List[Any]:
        """Generate actionable recommendations."""
        pass
