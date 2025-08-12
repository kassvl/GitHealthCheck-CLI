"""
Code quality analyzer for measuring various quality metrics.

Analyzes source code for complexity, maintainability, and quality indicators.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from ...models.report import CodeQualityMetrics, AnalysisConfig


class CodeQualityAnalyzer:
    """
    Analyzer for code quality metrics.
    
    Measures cyclomatic complexity, function length, comment density,
    naming consistency, and code duplication.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
    
    def analyze(self, source_files: List[Path]) -> CodeQualityMetrics:
        """
        Analyze code quality metrics for all source files.
        
        Args:
            source_files: List of source file paths
        
        Returns:
            CodeQualityMetrics: Comprehensive code quality metrics
        """
        all_metrics = {
            'complexity': [],
            'function_lengths': [],
            'comment_ratios': [],
            'naming_scores': [],
            'duplication_blocks': []
        }
        
        complexity_distribution = defaultdict(int)
        
        for file_path in source_files:
            try:
                file_metrics = self._analyze_file(file_path)
                
                # Aggregate metrics
                if file_metrics['complexity']:
                    all_metrics['complexity'].extend(file_metrics['complexity'])
                    
                    # Build complexity distribution
                    for complexity in file_metrics['complexity']:
                        if complexity <= 5:
                            complexity_distribution['low'] += 1
                        elif complexity <= 10:
                            complexity_distribution['medium'] += 1
                        elif complexity <= 20:
                            complexity_distribution['high'] += 1
                        else:
                            complexity_distribution['very_high'] += 1
                
                all_metrics['function_lengths'].extend(file_metrics['function_lengths'])
                all_metrics['comment_ratios'].append(file_metrics['comment_ratio'])
                all_metrics['naming_scores'].append(file_metrics['naming_score'])
                all_metrics['duplication_blocks'].extend(file_metrics['duplication_blocks'])
                
            except Exception as e:
                # Skip files that can't be analyzed
                continue
        
        # Calculate aggregate scores
        avg_complexity = sum(all_metrics['complexity']) / len(all_metrics['complexity']) if all_metrics['complexity'] else 0
        avg_function_length = sum(all_metrics['function_lengths']) / len(all_metrics['function_lengths']) if all_metrics['function_lengths'] else 0
        avg_comment_density = sum(all_metrics['comment_ratios']) / len(all_metrics['comment_ratios']) if all_metrics['comment_ratios'] else 0
        avg_naming_consistency = sum(all_metrics['naming_scores']) / len(all_metrics['naming_scores']) if all_metrics['naming_scores'] else 0
        
        # Calculate duplication ratio
        total_lines = sum(len(block) for block in all_metrics['duplication_blocks'])
        total_source_lines = sum(all_metrics['function_lengths']) * len(all_metrics['function_lengths'])
        duplication_ratio = total_lines / total_source_lines if total_source_lines > 0 else 0
        
        # Calculate overall score (0-10)
        complexity_score = max(0, 10 - (avg_complexity - 1) * 2)  # Penalize high complexity
        length_score = max(0, 10 - (avg_function_length - 20) / 5)  # Penalize long functions
        comment_score = min(10, avg_comment_density * 50)  # Reward good commenting
        naming_score = avg_naming_consistency * 10
        duplication_score = max(0, 10 - duplication_ratio * 50)  # Penalize duplication
        
        overall_score = (complexity_score + length_score + comment_score + naming_score + duplication_score) / 5
        
        return CodeQualityMetrics(
            overall_score=round(overall_score, 1),
            cyclomatic_complexity={
                'average': round(avg_complexity, 2),
                'max': max(all_metrics['complexity']) if all_metrics['complexity'] else 0,
                'functions_analyzed': len(all_metrics['complexity'])
            },
            function_length_avg=round(avg_function_length, 1),
            comment_density=round(avg_comment_density, 3),
            naming_consistency=round(avg_naming_consistency, 3),
            duplication_ratio=round(duplication_ratio, 3),
            complexity_distribution=dict(complexity_distribution)
        )
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single file for quality metrics.
        
        Args:
            file_path: Path to source file
        
        Returns:
            Dict: File-specific quality metrics
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return self._empty_metrics()
        
        # Language-specific analysis
        if file_path.suffix == '.py':
            return self._analyze_python_file(content)
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            return self._analyze_javascript_file(content)
        else:
            return self._analyze_generic_file(content)
    
    def _analyze_python_file(self, content: str) -> Dict[str, Any]:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            
            complexity_scores = []
            function_lengths = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calculate cyclomatic complexity
                    complexity = self._calculate_python_complexity(node)
                    complexity_scores.append(complexity)
                    
                    # Calculate function length
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        length = node.end_lineno - node.lineno + 1
                        function_lengths.append(length)
            
            # Calculate other metrics
            comment_ratio = self._calculate_comment_ratio(content)
            naming_score = self._calculate_python_naming_score(tree)
            duplication_blocks = self._find_duplication_blocks(content)
            
            return {
                'complexity': complexity_scores,
                'function_lengths': function_lengths,
                'comment_ratio': comment_ratio,
                'naming_score': naming_score,
                'duplication_blocks': duplication_blocks
            }
        
        except SyntaxError:
            return self._empty_metrics()
    
    def _analyze_javascript_file(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file using regex patterns."""
        # Simple regex-based analysis for JS/TS
        function_pattern = r'function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*\{)|class\s+\w+'
        functions = re.findall(function_pattern, content, re.MULTILINE)
        
        # Estimate complexity based on control flow keywords
        complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', '&&', '||', '?']
        complexity_count = sum(len(re.findall(rf'\b{keyword}\b', content)) for keyword in complexity_keywords)
        avg_complexity = complexity_count / max(len(functions), 1)
        
        # Estimate function lengths
        lines = content.split('\n')
        avg_function_length = len(lines) / max(len(functions), 1)
        
        comment_ratio = self._calculate_comment_ratio(content)
        naming_score = self._calculate_js_naming_score(content)
        duplication_blocks = self._find_duplication_blocks(content)
        
        return {
            'complexity': [avg_complexity] * len(functions) if functions else [],
            'function_lengths': [avg_function_length] * len(functions) if functions else [],
            'comment_ratio': comment_ratio,
            'naming_score': naming_score,
            'duplication_blocks': duplication_blocks
        }
    
    def _analyze_generic_file(self, content: str) -> Dict[str, Any]:
        """Generic analysis for other file types."""
        lines = content.split('\n')
        
        # Basic metrics
        comment_ratio = self._calculate_comment_ratio(content)
        
        return {
            'complexity': [],
            'function_lengths': [],
            'comment_ratio': comment_ratio,
            'naming_score': 0.7,  # Default neutral score
            'duplication_blocks': []
        }
    
    def _calculate_python_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.BoolOp,)):
                # Count AND/OR operations
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
        
        return complexity
    
    def _calculate_comment_ratio(self, content: str) -> float:
        """Calculate ratio of comment lines to total lines."""
        lines = content.split('\n')
        comment_lines = 0
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return 0.0
        
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*') or
                stripped.startswith('"""') or
                stripped.startswith("'''")):
                comment_lines += 1
        
        return comment_lines / total_lines
    
    def _calculate_python_naming_score(self, tree: ast.AST) -> float:
        """Calculate naming consistency score for Python code."""
        naming_violations = 0
        total_names = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_names += 1
                # Check snake_case for functions
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    naming_violations += 1
            
            elif isinstance(node, ast.ClassDef):
                total_names += 1
                # Check PascalCase for classes
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    naming_violations += 1
            
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                total_names += 1
                # Check snake_case for variables
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                    naming_violations += 1
        
        if total_names == 0:
            return 1.0
        
        return max(0, 1 - (naming_violations / total_names))
    
    def _calculate_js_naming_score(self, content: str) -> float:
        """Calculate naming consistency score for JavaScript/TypeScript."""
        # Simple regex-based naming analysis
        function_names = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=', content)
        class_names = re.findall(r'class\s+(\w+)', content)
        
        violations = 0
        total = 0
        
        # Check function names (camelCase)
        for match in function_names:
            name = match[0] or match[1]
            if name:
                total += 1
                if not re.match(r'^[a-z][a-zA-Z0-9]*$', name):
                    violations += 1
        
        # Check class names (PascalCase)
        for name in class_names:
            total += 1
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                violations += 1
        
        if total == 0:
            return 1.0
        
        return max(0, 1 - (violations / total))
    
    def _find_duplication_blocks(self, content: str) -> List[str]:
        """Find potential code duplication blocks."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Simple duplication detection: find repeated sequences of 3+ lines
        duplicates = []
        min_block_size = 3
        
        for i in range(len(lines) - min_block_size + 1):
            block = lines[i:i + min_block_size]
            block_str = '\n'.join(block)
            
            # Look for this block elsewhere in the file
            for j in range(i + min_block_size, len(lines) - min_block_size + 1):
                other_block = lines[j:j + min_block_size]
                if block == other_block:
                    duplicates.append(block_str)
                    break
        
        return duplicates
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics for files that can't be analyzed."""
        return {
            'complexity': [],
            'function_lengths': [],
            'comment_ratio': 0.0,
            'naming_score': 0.0,
            'duplication_blocks': []
        }
