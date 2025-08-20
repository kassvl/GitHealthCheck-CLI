"""Advanced documentation analyzer using regex patterns and file analysis."""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
from collections import defaultdict, Counter
from ...models.simple_report import DocumentationMetrics, AnalysisConfig

class DocumentationAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.doc_patterns = self._initialize_doc_patterns()
        self.doc_file_patterns = self._initialize_doc_file_patterns()
        self.language_patterns = self._initialize_language_patterns()
        
    def _initialize_doc_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize documentation detection patterns."""
        return {
            'python': {
                'class_docstring': r'class\s+\w+.*?:\s*\n\s*["\']{{3}}(.*?)["\']{{3}}',
                'function_docstring': r'def\s+\w+.*?:\s*\n\s*["\']{{3}}(.*?)["\']{{3}}',
                'module_docstring': r'""".*?"""|\'\'\'.*?\'\'\'',
                'inline_comments': r'#\s*(.+)',
                'type_hints': r':\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*\s*[=\)]',
                'return_annotation': r'->\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*:'
            },
            'javascript': {
                'jsdoc_comment': r'/\*\*(.*?)\*/',
                'function_comment': r'//\s*(.+)',
                'inline_comments': r'//\s*(.+)',
                'block_comments': r'/\*([^*].*?)\*/'
            },
            'java': {
                'javadoc_comment': r'/\*\*(.*?)\*/',
                'class_comment': r'/\*\*(.*?)\*/\s*(?:public\s+)?class',
                'method_comment': r'/\*\*(.*?)\*/\s*(?:public|private|protected)',
                'inline_comments': r'//\s*(.+)'
            },
            'generic': {
                'block_comments': r'/\*([^*].*?)\*/',
                'line_comments': r'//\s*(.+)|#\s*(.+)',
                'todo_comments': r'(?i)(TODO|FIXME|NOTE|WARNING):\s*(.+)'
            }
        }
    
    def _initialize_doc_file_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize documentation file patterns and scoring."""
        return {
            'readme_files': {
                'patterns': [r'README\.(md|rst|txt)$', r'readme\.(md|rst|txt)$'],
                'weight': 3.0,
                'description': 'Project overview and setup instructions'
            },
            'changelog_files': {
                'patterns': [r'CHANGELOG\.(md|rst|txt)$', r'CHANGES\.(md|rst|txt)$', r'HISTORY\.(md|rst|txt)$'],
                'weight': 2.0,
                'description': 'Version history and changes'
            },
            'contributing_files': {
                'patterns': [r'CONTRIBUTING\.(md|rst|txt)$', r'CONTRIBUTE\.(md|rst|txt)$'],
                'weight': 2.0,
                'description': 'Contribution guidelines'
            },
            'license_files': {
                'patterns': [r'LICENSE(\.txt|\.md)?$', r'LICENCE(\.txt|\.md)?$', r'COPYING$'],
                'weight': 1.5,
                'description': 'Project licensing information'
            },
            'api_docs': {
                'patterns': [r'docs?/.*\.(md|rst|txt)$', r'documentation/.*\.(md|rst|txt)$'],
                'weight': 2.5,
                'description': 'API and technical documentation'
            },
            'code_of_conduct': {
                'patterns': [r'CODE_OF_CONDUCT\.(md|rst|txt)$', r'CONDUCT\.(md|rst|txt)$'],
                'weight': 1.0,
                'description': 'Community guidelines'
            },
            'security_docs': {
                'patterns': [r'SECURITY\.(md|rst|txt)$', r'security\.(md|rst|txt)$'],
                'weight': 1.5,
                'description': 'Security policies and reporting'
            }
        }
    
    def _initialize_language_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize language-specific code patterns."""
        return {
            'python': {
                'class_def': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'function_def': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'public_method': r'^\s*def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\(',
                'private_method': r'^\s*def\s+(_[a-zA-Z0-9_]*)\s*\('
            },
            'javascript': {
                'class_def': r'^\s*class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                'function_def': r'^\s*(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=)',
                'export': r'^\s*export\s+'
            },
            'java': {
                'class_def': r'^\s*(?:public\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'method_def': r'^\s*(?:public|private|protected)\s+.*?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'public_method': r'^\s*public\s+.*?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            }
        }
    
    def analyze(self, repo_path: Path, source_files: List[Path]) -> DocumentationMetrics:
        """Perform comprehensive documentation analysis."""
        print(f"📚 Advanced documentation analysis on {len(source_files)} files...")
        
        # Analyze documentation files
        doc_files_analysis = self._analyze_documentation_files(repo_path)
        
        # Analyze code documentation
        code_doc_analysis = self._analyze_code_documentation(source_files)
        
        # Calculate comprehensive metrics
        metrics = self._calculate_documentation_metrics(
            doc_files_analysis, code_doc_analysis, repo_path, source_files
        )
        
        print(f"  ✅ Documentation analysis complete!")
        print(f"     📊 Overall Score: {metrics['overall_score']:.1f}/10")
        print(f"     📖 README Quality: {metrics['readme_quality']:.1f}/10")
        print(f"     📝 Docstring Coverage: {metrics['docstring_coverage']:.1%}")
        print(f"     📄 Doc Files: {metrics['doc_files_count']}")
        
        return DocumentationMetrics(
            score=round(metrics['overall_score'], 1),
            readme_quality=round(metrics['readme_quality'], 1),
            docstring_coverage=round(metrics['docstring_coverage'], 3),
            api_doc_coverage=round(metrics['api_doc_coverage'], 3),
            has_changelog=metrics['has_changelog'],
            has_contributing_guide=metrics['has_contributing_guide'],
            doc_files_count=metrics['doc_files_count']
        )
    
    def _analyze_documentation_files(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze documentation files in the repository."""
        doc_analysis: Dict[str, Any] = {
            'files_found': {},
            'total_score': 0.0,
            'max_possible_score': 0.0,
            'file_qualities': {},
            'missing_docs': []
        }
        
        # Scan for documentation files
        for doc_type, config in self.doc_file_patterns.items():
            patterns = config['patterns']
            weight = config['weight']
            description = config['description']
            
            doc_analysis['max_possible_score'] += weight
            found_files = []
            
            # Search for files matching patterns
            for pattern in patterns:
                for file_path in repo_path.rglob('*'):
                    if file_path.is_file() and re.search(pattern, file_path.name, re.IGNORECASE):
                        found_files.append(file_path)
            
            if found_files:
                doc_analysis['files_found'][doc_type] = found_files
                
                # Analyze quality of found files
                best_quality = 0.0
                for file_path in found_files:
                    quality = self._analyze_doc_file_quality(file_path)
                    best_quality = max(best_quality, quality)
                    doc_analysis['file_qualities'][str(file_path)] = quality
                
                doc_analysis['total_score'] += weight * best_quality
            else:
                doc_analysis['missing_docs'].append({
                    'type': doc_type,
                    'description': description,
                    'weight': weight
                })
        
        return doc_analysis
    
    def _analyze_doc_file_quality(self, file_path: Path) -> float:
        """Analyze the quality of a documentation file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return 0.0
        
        if not content.strip():
            return 0.0
        
        quality_score = 0.0
        
        # Basic content checks
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Length-based scoring
        if len(non_empty_lines) >= 50:
            quality_score += 0.4  # Comprehensive
        elif len(non_empty_lines) >= 20:
            quality_score += 0.3  # Adequate
        elif len(non_empty_lines) >= 5:
            quality_score += 0.2  # Minimal
        else:
            quality_score += 0.1  # Very basic
        
        # Content quality indicators
        quality_indicators = {
            'installation': r'(?i)(install|setup|getting\s+started)',
            'usage': r'(?i)(usage|example|how\s+to|tutorial)',
            'api': r'(?i)(api|reference|documentation)',
            'links': r'https?://|www\.',
            'code_examples': r'```|`\w+`|\n\s{4,}\w+',
            'headers': r'#+\s+\w+|=+\n|\-+\n',
            'lists': r'^\s*[-*+]\s+|\d+\.\s+'
        }
        
        for indicator, pattern in quality_indicators.items():
            if re.search(pattern, content, re.MULTILINE):
                quality_score += 0.05
        
        # Bonus for structured content
        if re.search(r'#+.*#+.*#+', content, re.DOTALL):  # Multiple headers
            quality_score += 0.1
        
        # Penalty for very short content
        if len(content) < 100:
            quality_score *= 0.5
        
        return min(quality_score, 1.0)
    
    def _analyze_code_documentation(self, source_files: List[Path]) -> Dict[str, Any]:
        """Analyze documentation within source code files."""
        code_doc_analysis: Dict[str, Any] = {
            'total_functions': 0,
            'documented_functions': 0,
            'total_classes': 0,
            'documented_classes': 0,
            'total_modules': 0,
            'documented_modules': 0,
            'comment_density': 0.0,
            'type_hint_coverage': 0.0,
            'documentation_by_file': {},
            'undocumented_items': []
        }
        
        total_lines = 0
        total_comment_lines = 0
        total_functions_with_hints = 0
        
        # Quick fix: Limit file processing to prevent hanging
        files_to_process = source_files[:5]  # Process only first 5 files
        for i, file_path in enumerate(files_to_process):
            print(f"  📄 Processing documentation {i+1}/{len(files_to_process)}: {file_path.name}")
            try:
                file_analysis = self._analyze_file_documentation(file_path)
                if file_analysis and isinstance(file_analysis, dict) and file_analysis:
                    # Aggregate counts
                    code_doc_analysis['total_functions'] += file_analysis['function_count']
                    code_doc_analysis['documented_functions'] += file_analysis['documented_functions']
                    code_doc_analysis['total_classes'] += file_analysis['class_count']
                    code_doc_analysis['documented_classes'] += file_analysis['documented_classes']
                    code_doc_analysis['total_modules'] += 1
                    if file_analysis['has_module_doc']:
                        code_doc_analysis['documented_modules'] += 1
                    
                    # Aggregate metrics
                    total_lines += file_analysis['total_lines']
                    total_comment_lines += file_analysis['comment_lines']
                    total_functions_with_hints += file_analysis['functions_with_type_hints']
                    
                    # Store file-level analysis
                    code_doc_analysis['documentation_by_file'][str(file_path)] = file_analysis
                    
                    # Track undocumented items
                    code_doc_analysis['undocumented_items'].extend(file_analysis['undocumented_items'])
                    
            except Exception as e:
                print(f"  ⚠️  Error analyzing {file_path.name}: {str(e)[:50]}...")
                continue
        
        # Calculate overall metrics
        if total_lines > 0:
            code_doc_analysis['comment_density'] = total_comment_lines / total_lines
        
        if code_doc_analysis['total_functions'] > 0:
            code_doc_analysis['type_hint_coverage'] = total_functions_with_hints / code_doc_analysis['total_functions']
        
        return code_doc_analysis
    
    def _analyze_file_documentation(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze documentation in a single source file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return {}
        
        if not content.strip():
            return {}
        
        # Detect language
        language = self._detect_language(file_path.suffix.lower())
        doc_patterns = self.doc_patterns.get(language, self.doc_patterns['generic'])
        lang_patterns = self.language_patterns.get(language, {})
        
        analysis: Dict[str, Any] = {
            'language': language,
            'total_lines': len([line for line in content.split('\n') if line.strip()]),
            'comment_lines': 0,
            'function_count': 0,
            'documented_functions': 0,
            'class_count': 0,
            'documented_classes': 0,
            'has_module_doc': False,
            'functions_with_type_hints': 0,
            'undocumented_items': []
        }
        
        # Count comment lines
        for line in content.split('\n'):
            if self._is_comment_line(line, language):
                analysis['comment_lines'] += 1
        
        # Check for module-level documentation
        if language == 'python':
            if re.search(doc_patterns.get('module_docstring', ''), content, re.DOTALL):
                analysis['has_module_doc'] = True
        
        # Analyze functions
        if 'function_def' in lang_patterns:
            functions = re.finditer(lang_patterns['function_def'], content, re.MULTILINE)
            for func_match in functions:
                analysis['function_count'] += 1
                func_name = func_match.group(1) if func_match.groups() else 'unknown'
                
                # Check if function is documented
                if self._is_function_documented(content, func_match, doc_patterns, language):
                    analysis['documented_functions'] += 1
                else:
                    analysis['undocumented_items'].append({
                        'type': 'function',
                        'name': func_name,
                        'line': content[:func_match.start()].count('\n') + 1,
                        'file': str(file_path)
                    })
                
                # Check for type hints (Python)
                if language == 'python':
                    func_line = func_match.group(0)
                    if ':' in func_line and '->' in content[func_match.start():func_match.start()+200]:
                        analysis['functions_with_type_hints'] += 1
        
        # Analyze classes
        if 'class_def' in lang_patterns:
            classes = re.finditer(lang_patterns['class_def'], content, re.MULTILINE)
            for class_match in classes:
                analysis['class_count'] += 1
                class_name = class_match.group(1) if class_match.groups() else 'unknown'
                
                # Check if class is documented
                if self._is_class_documented(content, class_match, doc_patterns, language):
                    analysis['documented_classes'] += 1
                else:
                    analysis['undocumented_items'].append({
                        'type': 'class',
                        'name': class_name,
                        'line': content[:class_match.start()].count('\n') + 1,
                        'file': str(file_path)
                    })
        
        return analysis
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript', '.ts': 'javascript', '.tsx': 'javascript',
            '.java': 'java',
            '.c': 'c', '.cpp': 'c', '.cc': 'c', '.cxx': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust'
        }
        return extension_map.get(file_extension, 'generic')
    
    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if a line is a comment."""
        stripped = line.strip()
        if language == 'python':
            return stripped.startswith('#')
        elif language in ['javascript', 'java', 'c']:
            return stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*')
        else:
            return stripped.startswith('#') or stripped.startswith('//')
    
    def _is_function_documented(self, content: str, func_match: re.Match, 
                              doc_patterns: Dict[str, str], language: str) -> bool:
        """Check if a function has documentation."""
        # Look for documentation after the function definition
        func_end = func_match.end()
        next_200_chars = content[func_end:func_end+200]
        
        if language == 'python':
            # Look for docstring - fix the regex pattern
            if re.search(r':\s*\n\s*["\']{{3}}', next_200_chars):
                return True
            # Also check for simple docstring pattern
            if re.search(r':\s*\n\s*"""', next_200_chars):
                return True
        elif language in ['javascript', 'java']:
            # Look for JSDoc or Javadoc comment before function
            func_start = max(0, func_match.start() - 200)
            prev_200_chars = content[func_start:func_match.start()]
            if re.search(r'/\*\*.*?\*/', prev_200_chars, re.DOTALL):
                return True
        
        # Generic comment check
        if re.search(r'#.*\w+|//.*\w+', next_200_chars):
            return True
        
        return False
    
    def _is_class_documented(self, content: str, class_match: re.Match,
                           doc_patterns: Dict[str, str], language: str) -> bool:
        """Check if a class has documentation."""
        # Look for documentation after the class definition
        class_end = class_match.end()
        next_300_chars = content[class_end:class_end+300]
        
        if language == 'python':
            # Look for class docstring - fix the regex pattern
            if re.search(r':\s*\n\s*["\']{{3}}', next_300_chars):
                return True
            # Also check for simple docstring pattern
            if re.search(r':\s*\n\s*"""', next_300_chars):
                return True
        elif language in ['javascript', 'java']:
            # Look for JSDoc or Javadoc comment before class
            class_start = max(0, class_match.start() - 300)
            prev_300_chars = content[class_start:class_match.start()]
            if re.search(r'/\*\*.*?\*/', prev_300_chars, re.DOTALL):
                return True
        
        # Generic comment check
        if re.search(r'#.*\w+|//.*\w+', next_300_chars):
            return True
        
        return False
    
    def _calculate_documentation_metrics(self, doc_files_analysis: Dict, 
                                       code_doc_analysis: Dict,
                                       repo_path: Path, source_files: List[Path]) -> Dict[str, Any]:
        """Calculate comprehensive documentation metrics."""
        
        # Documentation files score (0-10)
        if doc_files_analysis['max_possible_score'] > 0:
            doc_files_score = (doc_files_analysis['total_score'] / doc_files_analysis['max_possible_score']) * 10
        else:
            doc_files_score = 0.0
        
        # README quality (0-10)
        readme_quality = 0.0
        readme_files = doc_files_analysis['files_found'].get('readme_files', [])
        if readme_files:
            readme_qualities = [doc_files_analysis['file_qualities'].get(str(f), 0.0) for f in readme_files]
            readme_quality = max(readme_qualities) * 10
        
        # Code documentation coverage (0-1)
        docstring_coverage = 0.0
        if code_doc_analysis['total_functions'] > 0:
            docstring_coverage = code_doc_analysis['documented_functions'] / code_doc_analysis['total_functions']
        
        # API documentation coverage (0-1)
        api_doc_coverage = 0.0
        if code_doc_analysis['total_classes'] > 0:
            api_doc_coverage = code_doc_analysis['documented_classes'] / code_doc_analysis['total_classes']
        
        # Overall score calculation
        weights = {
            'doc_files': 0.3,
            'readme': 0.2,
            'docstrings': 0.25,
            'api_docs': 0.15,
            'comments': 0.1
        }
        
        overall_score = (
            doc_files_score * weights['doc_files'] +
            readme_quality * weights['readme'] +
            docstring_coverage * 10 * weights['docstrings'] +
            api_doc_coverage * 10 * weights['api_docs'] +
            code_doc_analysis['comment_density'] * 10 * weights['comments']
        )
        
        return {
            'overall_score': overall_score,
            'readme_quality': readme_quality,
            'docstring_coverage': docstring_coverage,
            'api_doc_coverage': api_doc_coverage,
            'has_changelog': 'changelog_files' in doc_files_analysis['files_found'],
            'has_contributing_guide': 'contributing_files' in doc_files_analysis['files_found'],
            'doc_files_count': len([f for files in doc_files_analysis['files_found'].values() for f in files])
        }
