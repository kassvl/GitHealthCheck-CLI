# Repo Health Analyzer (RHA)

A fully offline CLI and desktop application that analyzes local git repositories for comprehensive health metrics including code quality, architecture, code smells, test coverage, documentation quality, and sustainability prediction.

## Features

- **100% Offline Analysis** - No external APIs or internet required
- **Comprehensive Metrics** - Code quality, architecture, smells, tests, docs
- **ML-Powered Sustainability** - Predict 6-month active development probability
- **Cross-Platform** - Works on Windows, Linux, and macOS
- **Performance Optimized** - Handles repositories with 20k+ files efficiently
- **Rich Visualizations** - Optional heatmaps and dependency graphs

## Quick Start

### Installation

```bash
# Clone and install
git clone <repo-url>
cd repo-health-analyzer
pip install -e .

# Or install from PyPI (when available)
pip install repo-health-analyzer
```

### Basic Usage

```bash
# Analyze current directory
rha analyze

# Analyze specific repository
rha analyze /path/to/repo

# Generate with visualizations
rha analyze /path/to/repo --visualize

# Show detailed help
rha --help
```

## Architecture

```
repo_health_analyzer/
├── cli/                 # CLI interface and commands
├── core/               # Core analysis engines
│   ├── git_parser/     # Git repository parsing
│   ├── static_analyzer/ # Code quality and smell detection
│   ├── dependency/     # Dependency graph analysis
│   ├── test_analyzer/  # Test coverage analysis
│   └── docs_analyzer/  # Documentation quality analysis
├── ml/                 # ML models for sustainability prediction
├── visualization/      # Optional visualization generators
├── models/            # Data models and schemas
└── utils/             # Shared utilities
```

## Analysis Modules

### Code Quality Metrics
- Cyclomatic complexity
- Function length analysis
- Comment density
- Variable naming consistency
- Code duplication detection

### Architecture Analysis
- Dependency graph generation
- Single Responsibility Principle violations
- Circular dependency detection
- Module coupling analysis

### Code Smells Detection
- Long functions and god classes
- Excessive parameters
- Dead code detection
- Magic numbers and strings

### Test Analysis
- Test file detection
- Coverage analysis (when available)
- Test success rate tracking

### Documentation Quality
- Docstring completeness
- README quality assessment
- API documentation coverage

### Sustainability Prediction
- Commit pattern analysis
- Developer activity trends
- Repository maintenance probability

## Output Format

The tool generates a comprehensive JSON health report:

```json
{
  "repository": {
    "path": "/path/to/repo",
    "name": "example-repo",
    "analyzed_at": "2024-01-20T10:30:00Z"
  },
  "metrics": {
    "code_quality": {
      "overall_score": 8.5,
      "complexity": {...},
      "maintainability": {...}
    },
    "architecture": {
      "score": 7.2,
      "dependencies": {...},
      "violations": [...]
    },
    "code_smells": {
      "total_count": 15,
      "by_type": {...},
      "hotspots": [...]
    },
    "tests": {
      "coverage": 85.2,
      "test_files": 45,
      "success_rate": 98.5
    },
    "documentation": {
      "score": 6.8,
      "completeness": {...}
    },
    "sustainability": {
      "score": 7.9,
      "prediction": "high_maintenance_probability",
      "factors": [...]
    }
  },
  "recommendations": [...]
}
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy repo_health_analyzer/
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=repo_health_analyzer

# Specific test file
pytest tests/test_git_parser.py
```

## Performance

- Optimized for large repositories (20k+ files)
- Concurrent file processing
- Intelligent caching mechanisms
- Memory-efficient streaming for large files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
