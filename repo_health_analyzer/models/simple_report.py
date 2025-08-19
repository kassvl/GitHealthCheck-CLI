"""
Simple data classes without Pydantic for speed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class Priority(Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Recommendation:
    """A recommendation for improving code quality."""
    priority: Priority
    category: str
    description: str
    impact: str
    effort: str
    title: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    files_affected: List[str] = None
    
    def __post_init__(self):
        if self.files_affected is None:
            self.files_affected = []


@dataclass
class RepositoryInfo:
    path: str
    name: str
    analyzed_at: datetime = None
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, float] = None
    commit_count: int = 0
    contributors: List[str] = None
    age_days: int = 0
    branch: str = "main"
    total_commits: int = 0
    
    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()
        if self.languages is None:
            self.languages = {}
        if self.contributors is None:
            self.contributors = []


@dataclass
class CodeQualityMetrics:
    overall_score: float
    cyclomatic_complexity: Dict[str, float]
    function_length_avg: float
    comment_density: float
    naming_consistency: float
    duplication_ratio: float
    complexity_distribution: Dict[str, int]
    craftsmanship_score: float = 0.0
    type_hint_coverage: float = 0.0
    error_handling_density: float = 0.0
    todo_density: float = 0.0
    line_length_violations: float = 0.0
    indentation_consistency: float = 1.0


@dataclass
class ArchitectureMetrics:
    score: float
    dependency_count: int
    circular_dependencies: int
    coupling_score: float
    cohesion_score: float
    srp_violations: int
    module_count: int
    depth_of_inheritance: float


@dataclass
class CodeSmellMetrics:
    total_count: int
    severity_score: float
    smells_by_type: Dict[str, int]
    hotspot_files: List[str]
    smells: List[Any]


@dataclass
class TestMetrics:
    coverage_score: float
    test_files_count: int
    test_to_source_ratio: float
    test_success_rate: float
    has_coverage_report: bool
    coverage_percentage: Optional[float] = None
    uncovered_files: List[str] = None


@dataclass
class DocumentationMetrics:
    score: float
    readme_quality: float
    docstring_coverage: float
    api_doc_coverage: float
    has_changelog: bool
    has_contributing_guide: bool
    doc_files_count: int


@dataclass
class SustainabilityMetrics:
    score: float
    maintenance_probability: float
    activity_trend: str
    bus_factor: int
    recent_activity_score: float
    contributor_diversity: float
    commit_frequency_score: float


@dataclass
class OverallMetrics:
    overall_score: float
    code_quality: CodeQualityMetrics
    architecture: ArchitectureMetrics
    code_smells: CodeSmellMetrics
    tests: TestMetrics
    documentation: DocumentationMetrics
    sustainability: SustainabilityMetrics


@dataclass
class AnalysisConfig:
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_file_size_mb: int = 10
    enable_ml_prediction: bool = True
    complexity_threshold: int = 10
    function_length_threshold: int = 50
    parameter_count_threshold: int = 7
    duplication_threshold: float = 0.1
    
    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = ["*.py", "*.js", "*.ts"]
        if self.exclude_patterns is None:
            self.exclude_patterns = ["*/node_modules/*", "*/.git/*", "*/venv/*"]


@dataclass
class HealthReport:
    repository: RepositoryInfo
    metrics: OverallMetrics
    recommendations: List[Any]
    analysis_duration: float
    version: str = "0.1.0"
    
    def model_dump_json(self):
        import json
        return json.dumps(self.__dict__, default=str)
