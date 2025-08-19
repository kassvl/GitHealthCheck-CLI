"""Advanced test analyzer for comprehensive test coverage and quality assessment."""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
from collections import defaultdict, Counter
from ...models.simple_report import TestMetrics, AnalysisConfig

class TestAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.test_patterns = self._initialize_test_patterns()
        self.framework_patterns = self._initialize_framework_patterns()
        
    def _initialize_test_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize test file and function detection patterns."""
        return {
            'file_patterns': {
                'python': [
                    r'test_.*\.py$',
                    r'.*_test\.py$', 
                    r'.*/tests/.*\.py$',
                    r'.*/test/.*\.py$',
                    r'^test/.*\.py$',
                    r'conftest\.py$'
                ],
                'javascript': [
                    r'.*\.test\.js$',
                    r'.*\.spec\.js$',
                    r'.*\.test\.ts$',
                    r'.*\.spec\.ts$',
                    r'.*/tests?/.*\.js$',
                    r'^tests?/.*\.js$',
                    r'.*/spec/.*\.js$',
                    r'.*/__tests__/.*\.js$',
                    r'^__tests__/.*\.js$'
                ],
                'java': [
                    r'.*Test\.java$',
                    r'.*Tests\.java$',
                    r'.*/test/.*\.java$',
                    r'.*/tests/.*\.java$'
                ],
                'csharp': [
                    r'.*Test\.cs$',
                    r'.*Tests\.cs$',
                    r'.*/test/.*\.cs$',
                    r'.*/tests/.*\.cs$'
                ]
            },
            'function_patterns': {
                'python': [
                    r'^\s*def\s+test_\w+\s*\(',
                    r'^\s*@pytest\.mark\.',
                    r'^\s*def\s+\w+.*test.*\s*\(',
                    r'^\s*class\s+Test\w+\s*[\(:]',
                    r'^\s*def\s+(setUp|tearDown|setUpClass|tearDownClass)\s*\(',
                    r'^\s*@pytest\.fixture'
                ],
                'javascript': [
                    r'^\s*(?:it|test|describe)\s*\(',
                    r'^\s*(?:beforeEach|afterEach|beforeAll|afterAll)\s*\(',
                    r'^\s*expect\s*\(',
                    r'^\s*assert\s*\.'
                ],
                'java': [
                    r'^\s*@Test',
                    r'^\s*@BeforeEach',
                    r'^\s*@AfterEach',
                    r'^\s*@TestMethodOrder',
                    r'^\s*public\s+void\s+test\w+\s*\('
                ]
            },
            'assertion_patterns': {
                'python': [
                    r'assert\s+',
                    r'self\.assert\w+\(',
                    r'pytest\.raises\(',
                    r'mock\.assert_\w+\(',
                    r'expect\('
                ],
                'javascript': [
                    r'expect\s*\(',
                    r'assert\s*\.',
                    r'should\s*\.',
                    r'chai\.expect\(',
                    r'\.toBe\(',
                    r'\.toEqual\(',
                    r'\.toHaveBeenCalled\('
                ],
                'java': [
                    r'Assert\.\w+\(',
                    r'assertEquals\(',
                    r'assertTrue\(',
                    r'assertFalse\(',
                    r'assertNotNull\(',
                    r'assertThat\('
                ]
            }
        }
    
    def _initialize_framework_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize test framework detection patterns."""
        return {
            'python': {
                'pytest': r'import\s+pytest|from\s+pytest|@pytest\.',
                'unittest': r'import\s+unittest|from\s+unittest|unittest\.TestCase',
                'nose': r'import\s+nose|from\s+nose',
                'doctest': r'import\s+doctest|doctest\.',
                'tox': r'tox\.ini',
                'coverage': r'coverage\s+run|\.coveragerc|coverage\.py'
            },
            'javascript': {
                'jest': r'import.*jest|from.*jest|describe\(|it\(|test\(',
                'mocha': r'import.*mocha|from.*mocha|describe\(|it\(',
                'jasmine': r'import.*jasmine|from.*jasmine|describe\(|it\(',
                'cypress': r'cy\.|cypress|describe\(|it\(',
                'puppeteer': r'puppeteer|page\.|browser\.',
                'playwright': r'playwright|page\.|browser\.'
            },
            'java': {
                'junit': r'import\s+org\.junit|@Test|@BeforeEach|@AfterEach',
                'testng': r'import\s+org\.testng|@Test.*testng',
                'mockito': r'import.*mockito|@Mock|@Spy|@InjectMocks',
                'spring_test': r'@SpringBootTest|@WebMvcTest|@DataJpaTest'
            }
        }
    
    def analyze(self, source_files: List[Path]) -> TestMetrics:
        """Perform comprehensive test analysis."""
        print(f"🧪 Advanced test analysis on {len(source_files)} files...")
        
        # Separate test files from source files
        test_files, source_files_only = self._separate_test_files(source_files)
        
        # Analyze test files
        test_analysis = self._analyze_test_files(test_files)
        
        # Analyze test coverage patterns
        coverage_analysis = self._analyze_test_coverage(test_files, source_files_only)
        
        # Detect test frameworks
        framework_analysis = self._detect_test_frameworks(test_files)
        
        # Calculate comprehensive test metrics
        metrics = self._calculate_test_metrics(
            test_analysis, coverage_analysis, framework_analysis, 
            len(test_files), len(source_files_only)
        )
        
        print(f"  ✅ Test analysis complete!")
        print(f"     🧪 Test Files: {len(test_files)}")
        print(f"     📊 Coverage Score: {metrics['coverage_score']:.1f}/10")
        print(f"     📈 Test Ratio: {metrics['test_to_source_ratio']:.1%}")
        print(f"     🎯 Frameworks: {', '.join(framework_analysis['detected_frameworks'])}")
        
        return TestMetrics(
            coverage_score=round(metrics['coverage_score'], 1),
            test_files_count=len(test_files),
            test_to_source_ratio=round(metrics['test_to_source_ratio'], 3),
            test_success_rate=round(metrics['estimated_success_rate'], 3),
            has_coverage_report=metrics['has_coverage_indicators'],
            coverage_percentage=metrics['estimated_coverage'],
            uncovered_files=metrics['potentially_uncovered_files'][:20]  # Limit to 20
        )
    
    def _separate_test_files(self, all_files: List[Path]) -> Tuple[List[Path], List[Path]]:
        """Separate test files from source files."""
        test_files = []
        source_files = []
        
        for file_path in all_files:
            is_test_file = False
            file_str = str(file_path).lower()
            
            # Check against all language patterns
            for language, patterns in self.test_patterns['file_patterns'].items():
                for pattern in patterns:
                    if re.search(pattern, file_str):
                        is_test_file = True
                        break
                if is_test_file:
                    break
            
            if is_test_file:
                test_files.append(file_path)
            else:
                source_files.append(file_path)
        
        return test_files, source_files
    
    def _analyze_test_files(self, test_files: List[Path]) -> Dict[str, Any]:
        """Analyze test files for quality and coverage."""
        analysis: Dict[str, Any] = {
            'total_test_functions': 0,
            'total_assertions': 0,
            'test_classes': 0,
            'test_files_by_language': Counter(),
            'test_function_lengths': [],
            'assertion_density': [],
            'test_file_details': [],
            'setup_teardown_count': 0
        }
        
        for test_file in test_files:
            try:
                file_analysis = self._analyze_single_test_file(test_file)
                if file_analysis:
                    # Aggregate metrics
                    analysis['total_test_functions'] += file_analysis['test_functions']
                    analysis['total_assertions'] += file_analysis['assertions']
                    analysis['test_classes'] += file_analysis['test_classes']
                    analysis['setup_teardown_count'] += file_analysis['setup_teardown']
                    
                    # Track by language
                    analysis['test_files_by_language'][file_analysis['language']] += 1
                    
                    # Collect detailed metrics
                    analysis['test_function_lengths'].extend(file_analysis['function_lengths'])
                    analysis['assertion_density'].append(file_analysis['assertion_density'])
                    analysis['test_file_details'].append(file_analysis)
                    
            except Exception as e:
                print(f"  ⚠️  Error analyzing {test_file.name}: {str(e)[:50]}...")
                continue
        
        return analysis
    
    def _analyze_single_test_file(self, test_file: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single test file."""
        try:
            with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return None
        
        if not content.strip():
            return None
        
        # Detect language
        language = self._detect_language(test_file.suffix.lower())
        
        # Get patterns for this language
        function_patterns = self.test_patterns['function_patterns'].get(language, [])
        assertion_patterns = self.test_patterns['assertion_patterns'].get(language, [])
        
        analysis: Dict[str, Any] = {
            'file_path': str(test_file),
            'language': language,
            'total_lines': len([line for line in content.split('\n') if line.strip()]),
            'test_functions': 0,
            'test_classes': 0,
            'assertions': 0,
            'setup_teardown': 0,
            'function_lengths': [],
            'assertion_density': 0.0
        }
        
        # Count test functions and classes
        for pattern in function_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if 'class' in pattern.lower():
                analysis['test_classes'] += len(matches)
            elif any(keyword in pattern.lower() for keyword in ['before', 'after', 'setup', 'teardown', 'fixture']):
                analysis['setup_teardown'] += len(matches)
            else:
                analysis['test_functions'] += len(matches)
        
        # Count assertions
        for pattern in assertion_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            analysis['assertions'] += len(matches)
        
        # Calculate assertion density
        if analysis['total_lines'] > 0:
            analysis['assertion_density'] = analysis['assertions'] / analysis['total_lines']
        
        # Estimate function lengths (simplified)
        if analysis['test_functions'] > 0:
            avg_function_length = analysis['total_lines'] / analysis['test_functions']
            analysis['function_lengths'] = [avg_function_length] * analysis['test_functions']
        
        return analysis
    
    def _analyze_test_coverage(self, test_files: List[Path], source_files: List[Path]) -> Dict[str, Any]:
        """Analyze test coverage patterns."""
        coverage_analysis: Dict[str, Any] = {
            'has_coverage_config': False,
            'coverage_indicators': [],
            'potentially_uncovered_files': [],
            'test_to_source_mapping': {},
            'estimated_coverage_percentage': 0.0
        }
        
        # Check for coverage configuration files
        coverage_files = [
            '.coveragerc', 'coverage.cfg', '.coverage',
            'jest.config.js', 'jest.config.json',
            'karma.conf.js', 'nyc.config.js'
        ]
        
        if test_files:
            repo_root = test_files[0].parent
            while repo_root.parent != repo_root:
                for coverage_file in coverage_files:
                    if (repo_root / coverage_file).exists():
                        coverage_analysis['has_coverage_config'] = True
                        coverage_analysis['coverage_indicators'].append(coverage_file)
                repo_root = repo_root.parent
        
        # Analyze test-to-source file mapping
        test_source_pairs = 0
        for source_file in source_files:
            source_name = source_file.stem
            
            # Look for corresponding test files
            corresponding_tests = []
            for test_file in test_files:
                test_name = test_file.stem
                if (source_name in test_name.replace('test_', '').replace('_test', '') or
                    test_name.replace('test_', '').replace('_test', '') in source_name):
                    corresponding_tests.append(test_file)
            
            if corresponding_tests:
                test_source_pairs += 1
                coverage_analysis['test_to_source_mapping'][str(source_file)] = [str(t) for t in corresponding_tests]
            else:
                coverage_analysis['potentially_uncovered_files'].append(str(source_file))
        
        # Estimate coverage percentage
        if source_files:
            coverage_analysis['estimated_coverage_percentage'] = test_source_pairs / len(source_files)
        
        return coverage_analysis
    
    def _detect_test_frameworks(self, test_files: List[Path]) -> Dict[str, Any]:
        """Detect test frameworks used in the project."""
        framework_analysis: Dict[str, Any] = {
            'detected_frameworks': [],
            'framework_files': defaultdict(list),
            'framework_confidence': {}
        }
        
        framework_indicators: Counter[str] = Counter()
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                language = self._detect_language(test_file.suffix.lower())
                framework_patterns = self.framework_patterns.get(language, {})
                
                for framework, pattern in framework_patterns.items():
                    if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                        framework_indicators[framework] += 1
                        framework_analysis['framework_files'][framework].append(str(test_file))
                
            except Exception:
                continue
        
        # Determine detected frameworks with confidence scores
        total_files = len(test_files)
        for framework, count in framework_indicators.items():
            confidence = count / max(total_files, 1)
            if confidence >= 0.1:  # At least 10% of files use this framework
                framework_analysis['detected_frameworks'].append(framework)
                framework_analysis['framework_confidence'][framework] = confidence
        
        return framework_analysis
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.ts': 'javascript', '.tsx': 'javascript',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
            '.rb': 'ruby',
            '.php': 'php',
            '.go': 'go',
            '.rs': 'rust'
        }
        return extension_map.get(file_extension, 'generic')
    
    def _calculate_test_metrics(self, test_analysis: Dict, coverage_analysis: Dict,
                              framework_analysis: Dict, test_file_count: int,
                              source_file_count: int) -> Dict[str, Any]:
        """Calculate comprehensive test metrics."""
        
        # Test-to-source ratio
        test_to_source_ratio = test_file_count / max(source_file_count, 1) if source_file_count > 0 else 0
        
        # Coverage score (0-10 scale)
        coverage_factors = {
            'test_ratio': min(1.0, test_to_source_ratio * 2),  # Good ratio is 0.5+
            'assertion_density': min(1.0, test_analysis.get('total_assertions', 0) / max(test_analysis.get('total_test_functions', 1), 1) / 3),  # 3+ assertions per test
            'framework_usage': min(1.0, len(framework_analysis['detected_frameworks']) / 3),  # Using test frameworks
            'coverage_config': 1.0 if coverage_analysis['has_coverage_config'] else 0.0,
            'test_organization': min(1.0, test_analysis.get('test_classes', 0) / max(test_file_count, 1))  # Organized in classes
        }
        
        # Weighted coverage score
        weights = {
            'test_ratio': 0.3,
            'assertion_density': 0.25,
            'framework_usage': 0.2,
            'coverage_config': 0.15,
            'test_organization': 0.1
        }
        
        coverage_score = sum(coverage_factors[factor] * weights[factor] for factor in weights) * 10
        
        # Estimated success rate (based on assertion density and organization)
        success_rate = min(1.0, (
            coverage_factors['assertion_density'] * 0.4 +
            coverage_factors['framework_usage'] * 0.3 +
            coverage_factors['test_organization'] * 0.3
        ))
        
        # Adjust success rate based on test function lengths
        if test_analysis.get('test_function_lengths'):
            avg_test_length = sum(test_analysis['test_function_lengths']) / len(test_analysis['test_function_lengths'])
            if avg_test_length > 50:  # Very long tests might be less reliable
                success_rate *= 0.9
            elif avg_test_length < 5:  # Very short tests might be incomplete
                success_rate *= 0.8
        
        return {
            'coverage_score': coverage_score,
            'test_to_source_ratio': test_to_source_ratio,
            'estimated_success_rate': max(0.5, success_rate),  # Minimum 50% estimated success
            'has_coverage_indicators': coverage_analysis.get('has_coverage_config', False) or len(coverage_analysis.get('coverage_indicators', [])) > 0,
            'estimated_coverage': coverage_analysis.get('estimated_coverage_percentage', 0.0),
            'potentially_uncovered_files': coverage_analysis.get('potentially_uncovered_files', [])
        }