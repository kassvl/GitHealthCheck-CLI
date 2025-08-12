"""
Test coverage analyzer for evaluating test quality and coverage.

Analyzes test files, coverage reports, and test-to-source ratios.
"""

import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...models.report import TestMetrics, AnalysisConfig


class TestAnalyzer:
    """
    Analyzer for test coverage and quality metrics.
    
    Evaluates test presence, coverage reports, and test quality indicators.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
    
    def analyze(self, repo_path: Path, source_files: List[Path]) -> TestMetrics:
        """
        Analyze test coverage and quality.
        
        Args:
            repo_path: Repository root path
            source_files: List of source file paths
        
        Returns:
            TestMetrics: Test coverage and quality metrics
        """
        # Identify test files
        test_files = self._identify_test_files(source_files)
        
        # Calculate test-to-source ratio
        source_file_count = len([f for f in source_files if not self._is_test_file(f)])
        test_to_source_ratio = len(test_files) / max(source_file_count, 1)
        
        # Look for coverage reports
        coverage_info = self._find_coverage_reports(repo_path)
        
        # Estimate test success rate
        test_success_rate = self._estimate_test_success_rate(test_files)
        
        # Calculate coverage score
        coverage_score = self._calculate_coverage_score(
            test_to_source_ratio, coverage_info, test_success_rate
        )
        
        return TestMetrics(
            coverage_score=round(coverage_score, 1),
            test_files_count=len(test_files),
            test_to_source_ratio=round(test_to_source_ratio, 3),
            test_success_rate=round(test_success_rate, 3),
            has_coverage_report=coverage_info['has_report'],
            coverage_percentage=coverage_info.get('percentage'),
            uncovered_files=coverage_info.get('uncovered_files', [])
        )
    
    def _identify_test_files(self, source_files: List[Path]) -> List[Path]:
        """Identify test files from source files."""
        test_files = []
        
        for file_path in source_files:
            if self._is_test_file(file_path):
                test_files.append(file_path)
        
        return test_files
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file."""
        name = file_path.name.lower()
        path_str = str(file_path).lower()
        
        # Common test file patterns
        test_indicators = [
            name.startswith('test_'),
            name.endswith('_test.py'),
            name.endswith('.test.js'),
            name.endswith('.test.ts'),
            name.endswith('.spec.js'),
            name.endswith('.spec.ts'),
            '/test/' in path_str,
            '/tests/' in path_str,
            '/__tests__/' in path_str,
            '/spec/' in path_str
        ]
        
        return any(test_indicators)
    
    def _find_coverage_reports(self, repo_path: Path) -> Dict[str, Any]:
        """Find and parse coverage reports."""
        coverage_info = {'has_report': False}
        
        # Look for common coverage report files
        coverage_files = [
            'coverage.xml',
            'coverage.json',
            '.coverage',
            'htmlcov/index.html',
            'coverage/lcov.info',
            'coverage/coverage-final.json'
        ]
        
        for coverage_file in coverage_files:
            coverage_path = repo_path / coverage_file
            if coverage_path.exists():
                coverage_info['has_report'] = True
                
                # Try to parse coverage percentage
                if coverage_file == 'coverage.xml':
                    percentage = self._parse_xml_coverage(coverage_path)
                    if percentage:
                        coverage_info['percentage'] = percentage
                
                elif coverage_file == 'coverage.json':
                    percentage = self._parse_json_coverage(coverage_path)
                    if percentage:
                        coverage_info['percentage'] = percentage
                
                break
        
        return coverage_info
    
    def _parse_xml_coverage(self, coverage_path: Path) -> Optional[float]:
        """Parse XML coverage report (e.g., from coverage.py)."""
        try:
            tree = ET.parse(coverage_path)
            root = tree.getroot()
            
            # Look for coverage percentage in XML
            coverage_elem = root.find('.//coverage')
            if coverage_elem is not None:
                line_rate = coverage_elem.get('line-rate')
                if line_rate:
                    return float(line_rate) * 100
            
            # Alternative: look in summary
            for elem in root.iter():
                if 'line-rate' in elem.attrib:
                    return float(elem.attrib['line-rate']) * 100
        
        except Exception:
            pass
        
        return None
    
    def _parse_json_coverage(self, coverage_path: Path) -> Optional[float]:
        """Parse JSON coverage report."""
        try:
            with open(coverage_path, 'r') as f:
                data = json.load(f)
            
            # Look for total coverage percentage
            if 'total' in data and 'lines' in data['total']:
                return data['total']['lines']['pct']
            
            # Alternative structures
            if 'percent_covered' in data:
                return data['percent_covered']
        
        except Exception:
            pass
        
        return None
    
    def _estimate_test_success_rate(self, test_files: List[Path]) -> float:
        """Estimate test success rate based on test file analysis."""
        if not test_files:
            return 0.0
        
        # This is a simplified estimation
        # In a real implementation, you'd run the tests or parse test results
        
        total_tests = 0
        potential_issues = 0
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count test functions/methods
                if test_file.suffix == '.py':
                    test_count = len(re.findall(r'def\s+test_\w+', content))
                    total_tests += test_count
                    
                    # Look for potential issues (skip, todo, fixme)
                    issues = len(re.findall(r'@pytest\.mark\.skip|TODO|FIXME|XXX', content, re.IGNORECASE))
                    potential_issues += issues
                
                elif test_file.suffix in ['.js', '.ts']:
                    test_count = len(re.findall(r'it\s*\(|test\s*\(|describe\s*\(', content))
                    total_tests += test_count
                    
                    issues = len(re.findall(r'\.skip\s*\(|TODO|FIXME|XXX', content, re.IGNORECASE))
                    potential_issues += issues
            
            except Exception:
                continue
        
        if total_tests == 0:
            return 0.0
        
        # Estimate success rate (assume most tests pass unless there are obvious issues)
        estimated_failures = min(potential_issues, total_tests * 0.1)  # Cap at 10% failure rate
        success_rate = (total_tests - estimated_failures) / total_tests
        
        return max(0.0, min(1.0, success_rate))
    
    def _calculate_coverage_score(
        self, test_ratio: float, coverage_info: Dict[str, Any], success_rate: float
    ) -> float:
        """Calculate overall test coverage score (0-10)."""
        
        # Base score from test-to-source ratio
        ratio_score = min(10, test_ratio * 20)  # 0.5 ratio = 10 points
        
        # Coverage report bonus
        coverage_score = 0
        if coverage_info['has_report']:
            coverage_score += 2  # Bonus for having coverage reports
            
            if 'percentage' in coverage_info:
                coverage_pct = coverage_info['percentage']
                coverage_score += (coverage_pct / 100) * 6  # Up to 6 points for 100% coverage
        
        # Success rate factor
        success_score = success_rate * 2  # Up to 2 points for 100% success
        
        total_score = ratio_score + coverage_score + success_score
        
        return min(10, total_score)
