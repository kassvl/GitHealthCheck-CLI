"""
Code smell detector for identifying problematic code patterns.

Detects various code smells including long functions, god classes,
excessive parameters, and other maintainability issues.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from ...models.report import CodeSmellMetrics, CodeSmell, SmellType, AnalysisConfig


class CodeSmellDetector:
    """
    Detector for various code smells and anti-patterns.
    
    Identifies maintainability issues that can impact code quality
    and team productivity.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
    
    def analyze(self, source_files: List[Path]) -> CodeSmellMetrics:
        """
        Detect code smells across all source files.
        
        Args:
            source_files: List of source file paths
        
        Returns:
            CodeSmellMetrics: Detected code smells and metrics
        """
        all_smells = []
        smells_by_type = defaultdict(int)
        file_smell_counts = defaultdict(int)
        
        for file_path in source_files:
            try:
                file_smells = self._analyze_file(file_path)
                all_smells.extend(file_smells)
                
                # Count smells by type and file
                for smell in file_smells:
                    smells_by_type[smell.type] += 1
                    file_smell_counts[smell.file_path] += 1
                
            except Exception:
                continue
        
        # Identify hotspot files (files with most smells)
        hotspot_files = sorted(
            file_smell_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Calculate severity score (0-10, higher = more severe)
        total_severity = sum(smell.severity for smell in all_smells)
        avg_severity = total_severity / len(all_smells) if all_smells else 0
        
        return CodeSmellMetrics(
            total_count=len(all_smells),
            severity_score=round(avg_severity, 1),
            smells_by_type=dict(smells_by_type),
            hotspot_files=[file_path for file_path, _ in hotspot_files],
            smells=all_smells
        )
    
    def _analyze_file(self, file_path: Path) -> List[CodeSmell]:
        """
        Analyze a single file for code smells.
        
        Args:
            file_path: Path to source file
        
        Returns:
            List[CodeSmell]: List of detected code smells
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return []
        
        smells = []
        
        if file_path.suffix == '.py':
            smells.extend(self._analyze_python_smells(file_path, content))
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            smells.extend(self._analyze_javascript_smells(file_path, content))
        else:
            smells.extend(self._analyze_generic_smells(file_path, content))
        
        return smells
    
    def _analyze_python_smells(self, file_path: Path, content: str) -> List[CodeSmell]:
        """Detect code smells in Python files using AST."""
        smells = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    smells.extend(self._check_python_function_smells(file_path, node, content))
                
                elif isinstance(node, ast.ClassDef):
                    smells.extend(self._check_python_class_smells(file_path, node, content))
        
        except SyntaxError:
            pass
        
        # Add generic smells
        smells.extend(self._check_magic_numbers(file_path, content))
        smells.extend(self._check_dead_code(file_path, content))
        
        return smells
    
    def _analyze_javascript_smells(self, file_path: Path, content: str) -> List[CodeSmell]:
        """Detect code smells in JavaScript/TypeScript files."""
        smells = []
        
        # Function length analysis
        function_pattern = r'function\s+\w+\s*\([^)]*\)\s*\{|const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{'
        functions = list(re.finditer(function_pattern, content, re.MULTILINE))
        
        lines = content.split('\n')
        
        for match in functions:
            start_line = content[:match.start()].count('\n') + 1
            
            # Find function end (simplified)
            brace_count = 0
            end_line = start_line
            for i, line in enumerate(lines[start_line-1:], start_line):
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and i > start_line:
                    end_line = i
                    break
            
            function_length = end_line - start_line + 1
            
            if function_length > self.config.function_length_threshold:
                smells.append(CodeSmell(
                    type=SmellType.LONG_FUNCTION,
                    file_path=str(file_path),
                    line_number=start_line,
                    severity=min(10, function_length / 10),
                    description=f"Function is {function_length} lines long",
                    suggestion="Consider breaking this function into smaller functions"
                ))
        
        # Add generic smells
        smells.extend(self._check_magic_numbers(file_path, content))
        
        return smells
    
    def _analyze_generic_smells(self, file_path: Path, content: str) -> List[CodeSmell]:
        """Detect language-agnostic code smells."""
        smells = []
        
        # Check for very long files
        lines = content.split('\n')
        if len(lines) > 1000:
            smells.append(CodeSmell(
                type=SmellType.GOD_CLASS,
                file_path=str(file_path),
                line_number=1,
                severity=min(10, len(lines) / 200),
                description=f"File is very long ({len(lines)} lines)",
                suggestion="Consider splitting this file into smaller modules"
            ))
        
        smells.extend(self._check_magic_numbers(file_path, content))
        
        return smells
    
    def _check_python_function_smells(self, file_path: Path, node: ast.FunctionDef, content: str) -> List[CodeSmell]:
        """Check Python function for various smells."""
        smells = []
        
        # Long function
        if hasattr(node, 'end_lineno') and node.end_lineno:
            length = node.end_lineno - node.lineno + 1
            if length > self.config.function_length_threshold:
                smells.append(CodeSmell(
                    type=SmellType.LONG_FUNCTION,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    severity=min(10, length / 10),
                    description=f"Function '{node.name}' is {length} lines long",
                    suggestion="Consider breaking this function into smaller functions"
                ))
        
        # Excessive parameters
        param_count = len(node.args.args) + len(node.args.kwonlyargs)
        if param_count > self.config.parameter_count_threshold:
            smells.append(CodeSmell(
                type=SmellType.EXCESSIVE_PARAMETERS,
                file_path=str(file_path),
                line_number=node.lineno,
                severity=min(10, param_count / 2),
                description=f"Function '{node.name}' has {param_count} parameters",
                suggestion="Consider using a parameter object or reducing parameters"
            ))
        
        # Complex conditionals
        complexity = self._calculate_conditional_complexity(node)
        if complexity > 5:
            smells.append(CodeSmell(
                type=SmellType.COMPLEX_CONDITIONAL,
                file_path=str(file_path),
                line_number=node.lineno,
                severity=min(10, complexity / 2),
                description=f"Function '{node.name}' has complex conditional logic",
                suggestion="Simplify conditional logic or extract to separate functions"
            ))
        
        return smells
    
    def _check_python_class_smells(self, file_path: Path, node: ast.ClassDef, content: str) -> List[CodeSmell]:
        """Check Python class for god class smell."""
        smells = []
        
        # Count methods and lines
        method_count = 0
        total_lines = 0
        
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_count += 1
                if hasattr(child, 'end_lineno') and child.end_lineno:
                    total_lines += child.end_lineno - child.lineno + 1
        
        # God class detection
        if method_count > 20 or total_lines > 500:
            severity = min(10, (method_count / 5) + (total_lines / 100))
            smells.append(CodeSmell(
                type=SmellType.GOD_CLASS,
                file_path=str(file_path),
                line_number=node.lineno,
                severity=severity,
                description=f"Class '{node.name}' has {method_count} methods and {total_lines} lines",
                suggestion="Consider splitting this class into smaller, more focused classes"
            ))
        
        return smells
    
    def _check_magic_numbers(self, file_path: Path, content: str) -> List[CodeSmell]:
        """Detect magic numbers in code."""
        smells = []
        
        # Find numeric literals (excluding common ones like 0, 1, -1)
        number_pattern = r'\b(?<![\w.])[2-9]\d*(?:\.\d+)?\b(?![\w.])'
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(number_pattern, line)
            for match in matches:
                number = match.group()
                # Skip common numbers
                if number in ['2', '10', '100', '1000']:
                    continue
                
                smells.append(CodeSmell(
                    type=SmellType.MAGIC_NUMBER,
                    file_path=str(file_path),
                    line_number=line_num,
                    severity=3.0,
                    description=f"Magic number '{number}' found",
                    suggestion="Consider defining this as a named constant"
                ))
        
        return smells
    
    def _check_dead_code(self, file_path: Path, content: str) -> List[CodeSmell]:
        """Detect potential dead code."""
        smells = []
        
        # Look for commented-out code blocks
        lines = content.split('\n')
        consecutive_comments = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('#') or stripped.startswith('//'):
                # Check if this looks like commented code
                uncommented = stripped[1:].strip()
                if (any(keyword in uncommented for keyword in ['def ', 'class ', 'function ', 'var ', 'const ', 'if ', 'for ', 'while ']) or
                    re.match(r'^[a-zA-Z_]\w*\s*[=(){}]', uncommented)):
                    consecutive_comments += 1
                else:
                    consecutive_comments = 0
            else:
                if consecutive_comments >= 3:
                    smells.append(CodeSmell(
                        type=SmellType.DEAD_CODE,
                        file_path=str(file_path),
                        line_number=line_num - consecutive_comments,
                        severity=4.0,
                        description=f"Potential dead code block ({consecutive_comments} lines)",
                        suggestion="Remove commented-out code or document why it's kept"
                    ))
                consecutive_comments = 0
        
        return smells
    
    def _calculate_conditional_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of conditional statements."""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
