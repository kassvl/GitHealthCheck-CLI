"""
Helper utilities for repository analysis.

Common utility functions used across different analysis modules.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Set, Dict, Any


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to file
    
    Returns:
        str: Hexadecimal hash string
    """
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def extract_functions_from_python(content: str) -> List[Dict[str, Any]]:
    """
    Extract function definitions from Python code.
    
    Args:
        content: Python source code
    
    Returns:
        List[Dict]: Function metadata
    """
    import ast
    
    functions = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': getattr(node, 'end_lineno', node.lineno),
                    'args_count': len(node.args.args),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'has_docstring': (
                        node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                    )
                })
    
    except SyntaxError:
        pass
    
    return functions


def extract_classes_from_python(content: str) -> List[Dict[str, Any]]:
    """
    Extract class definitions from Python code.
    
    Args:
        content: Python source code
    
    Returns:
        List[Dict]: Class metadata
    """
    import ast
    
    classes = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': getattr(node, 'end_lineno', node.lineno),
                    'methods_count': len(methods),
                    'base_classes': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                    'has_docstring': (
                        node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                    )
                })
    
    except SyntaxError:
        pass
    
    return classes


def extract_imports_from_python(content: str) -> Set[str]:
    """
    Extract import statements from Python code.
    
    Args:
        content: Python source code
    
    Returns:
        Set[str]: Set of imported module names
    """
    import ast
    
    imports = set()
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    
    except SyntaxError:
        # Fallback to regex
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.update(match.split('.')[0] for match in matches)
    
    return imports


def calculate_lines_of_code(content: str) -> Dict[str, int]:
    """
    Calculate different types of lines in source code.
    
    Args:
        content: Source code content
    
    Returns:
        Dict: Line count statistics
    """
    lines = content.split('\n')
    
    total_lines = len(lines)
    blank_lines = len([line for line in lines if not line.strip()])
    comment_lines = 0
    code_lines = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        elif (stripped.startswith('#') or 
              stripped.startswith('//') or 
              stripped.startswith('/*') or 
              stripped.startswith('*')):
            comment_lines += 1
        else:
            code_lines += 1
    
    return {
        'total': total_lines,
        'code': code_lines,
        'comments': comment_lines,
        'blank': blank_lines
    }


def normalize_path(path: Path, base_path: Path) -> str:
    """
    Normalize file path relative to base path.
    
    Args:
        path: File path to normalize
        base_path: Base path for relative calculation
    
    Returns:
        str: Normalized relative path
    """
    try:
        return str(path.relative_to(base_path))
    except ValueError:
        return str(path)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division by zero
    
    Returns:
        float: Division result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float = 0.0, max_val: float = 10.0) -> float:
    """
    Clamp value between min and max bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum bound
        max_val: Maximum bound
    
    Returns:
        float: Clamped value
    """
    return max(min_val, min(max_val, value))


def find_files_by_pattern(directory: Path, patterns: List[str]) -> List[Path]:
    """
    Find files matching patterns in directory.
    
    Args:
        directory: Directory to search
        patterns: List of glob patterns
    
    Returns:
        List[Path]: Matching file paths
    """
    import fnmatch
    
    matching_files = []
    
    for root, _, files in directory.walk():
        for file in files:
            file_path = root / file
            
            for pattern in patterns:
                if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                    matching_files.append(file_path)
                    break
    
    return matching_files


def estimate_complexity_from_keywords(content: str) -> int:
    """
    Estimate code complexity based on control flow keywords.
    
    Args:
        content: Source code content
    
    Returns:
        int: Estimated complexity score
    """
    keywords = ['if', 'elif', 'else', 'while', 'for', 'try', 'except', 'finally', 'with']
    complexity = 1  # Base complexity
    
    for keyword in keywords:
        # Count keyword occurrences
        pattern = rf'\b{keyword}\b'
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        complexity += matches
    
    return complexity
