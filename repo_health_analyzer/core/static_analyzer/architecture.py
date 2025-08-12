"""
Architecture analyzer for dependency analysis and design quality.

Analyzes module dependencies, coupling, cohesion, and architectural patterns.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

import networkx as nx

from ...models.report import ArchitectureMetrics, AnalysisConfig


class ArchitectureAnalyzer:
    """
    Analyzer for software architecture and design quality.
    
    Builds dependency graphs and measures architectural quality metrics
    including coupling, cohesion, and design principle violations.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.dependency_graph = nx.DiGraph()
    
    def analyze(self, source_files: List[Path]) -> ArchitectureMetrics:
        """
        Analyze architecture and design quality.
        
        Args:
            source_files: List of source file paths
        
        Returns:
            ArchitectureMetrics: Architecture quality metrics
        """
        # Build dependency graph
        self._build_dependency_graph(source_files)
        
        # Calculate metrics
        dependency_count = len(self.dependency_graph.edges())
        circular_dependencies = len(list(nx.simple_cycles(self.dependency_graph)))
        module_count = len(self.dependency_graph.nodes())
        
        # Calculate coupling and cohesion
        coupling_score = self._calculate_coupling_score()
        cohesion_score = self._calculate_cohesion_score(source_files)
        
        # Detect SRP violations
        srp_violations = self._detect_srp_violations(source_files)
        
        # Calculate depth of inheritance
        inheritance_depth = self._calculate_inheritance_depth(source_files)
        
        # Calculate overall architecture score
        score = self._calculate_architecture_score(
            coupling_score, cohesion_score, circular_dependencies,
            srp_violations, dependency_count, module_count
        )
        
        return ArchitectureMetrics(
            score=round(score, 1),
            dependency_count=dependency_count,
            circular_dependencies=circular_dependencies,
            coupling_score=round(coupling_score, 2),
            cohesion_score=round(cohesion_score, 2),
            srp_violations=srp_violations,
            module_count=module_count,
            depth_of_inheritance=round(inheritance_depth, 1)
        )
    
    def _build_dependency_graph(self, source_files: List[Path]) -> None:
        """Build dependency graph from import statements."""
        for file_path in source_files:
            try:
                dependencies = self._extract_dependencies(file_path)
                module_name = self._get_module_name(file_path)
                
                self.dependency_graph.add_node(module_name)
                
                for dep in dependencies:
                    self.dependency_graph.add_edge(module_name, dep)
            
            except Exception:
                continue
    
    def _extract_dependencies(self, file_path: Path) -> Set[str]:
        """Extract import dependencies from a file."""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return dependencies
        
        if file_path.suffix == '.py':
            dependencies.update(self._extract_python_imports(content))
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            dependencies.update(self._extract_javascript_imports(content))
        
        return dependencies
    
    def _extract_python_imports(self, content: str) -> Set[str]:
        """Extract Python import statements."""
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
            # Fallback to regex for invalid syntax
            import_patterns = [
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.update(match.split('.')[0] for match in matches)
        
        return imports
    
    def _extract_javascript_imports(self, content: str) -> Set[str]:
        """Extract JavaScript/TypeScript import statements."""
        imports = set()
        
        # ES6 imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # Extract module name (remove relative paths)
                module = match.split('/')[0] if not match.startswith('.') else match
                imports.add(module)
        
        return imports
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        # Remove extension and convert path separators
        module_parts = file_path.with_suffix('').parts
        return '.'.join(module_parts)
    
    def _calculate_coupling_score(self) -> float:
        """Calculate coupling score (0-10, lower is better)."""
        if not self.dependency_graph.nodes():
            return 0.0
        
        # Calculate average out-degree (dependencies per module)
        total_dependencies = sum(self.dependency_graph.out_degree(node) 
                               for node in self.dependency_graph.nodes())
        avg_dependencies = total_dependencies / len(self.dependency_graph.nodes())
        
        # Convert to 0-10 scale (higher dependencies = higher coupling = higher score)
        coupling_score = min(10, avg_dependencies)
        
        return coupling_score
    
    def _calculate_cohesion_score(self, source_files: List[Path]) -> float:
        """Calculate cohesion score (0-10, higher is better)."""
        # Simplified cohesion calculation based on function relationships
        total_cohesion = 0
        analyzed_files = 0
        
        for file_path in source_files:
            if file_path.suffix == '.py':
                cohesion = self._calculate_python_cohesion(file_path)
                if cohesion >= 0:
                    total_cohesion += cohesion
                    analyzed_files += 1
        
        if analyzed_files == 0:
            return 7.0  # Default neutral score
        
        return total_cohesion / analyzed_files
    
    def _calculate_python_cohesion(self, file_path: Path) -> float:
        """Calculate cohesion for a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find all classes
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            if not classes:
                return -1  # No classes to analyze
            
            total_cohesion = 0
            
            for class_node in classes:
                methods = [node for node in class_node.body 
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                if len(methods) < 2:
                    total_cohesion += 10  # Single method = perfect cohesion
                    continue
                
                # Calculate how many methods use instance variables
                instance_var_usage = defaultdict(int)
                
                for method in methods:
                    for node in ast.walk(method):
                        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                            if node.value.id == 'self':
                                instance_var_usage[node.attr] += 1
                
                # Cohesion = average usage of instance variables across methods
                if instance_var_usage:
                    avg_usage = sum(instance_var_usage.values()) / len(instance_var_usage)
                    cohesion = min(10, avg_usage * 2)
                else:
                    cohesion = 2  # Low cohesion if no shared state
                
                total_cohesion += cohesion
            
            return total_cohesion / len(classes)
        
        except Exception:
            return -1
    
    def _detect_srp_violations(self, source_files: List[Path]) -> int:
        """Detect Single Responsibility Principle violations."""
        violations = 0
        
        for file_path in source_files:
            if file_path.suffix == '.py':
                violations += self._check_python_srp(file_path)
        
        return violations
    
    def _check_python_srp(self, file_path: Path) -> int:
        """Check Python file for SRP violations."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            violations = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class has too many responsibilities
                    method_purposes = self._categorize_methods(node)
                    
                    # If class has methods from more than 2 categories, it might violate SRP
                    if len(method_purposes) > 2:
                        violations += 1
            
            return violations
        
        except Exception:
            return 0
    
    def _categorize_methods(self, class_node: ast.ClassDef) -> Set[str]:
        """Categorize methods by their apparent purpose."""
        categories = set()
        
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name.lower()
                
                if any(prefix in name for prefix in ['get_', 'fetch_', 'read_', 'load_']):
                    categories.add('data_access')
                elif any(prefix in name for prefix in ['set_', 'save_', 'write_', 'store_']):
                    categories.add('data_storage')
                elif any(prefix in name for prefix in ['validate_', 'check_', 'verify_']):
                    categories.add('validation')
                elif any(prefix in name for prefix in ['format_', 'render_', 'display_']):
                    categories.add('presentation')
                elif any(prefix in name for prefix in ['calculate_', 'compute_', 'process_']):
                    categories.add('computation')
                else:
                    categories.add('business_logic')
        
        return categories
    
    def _calculate_inheritance_depth(self, source_files: List[Path]) -> float:
        """Calculate average inheritance depth."""
        depths = []
        
        for file_path in source_files:
            if file_path.suffix == '.py':
                file_depths = self._get_python_inheritance_depths(file_path)
                depths.extend(file_depths)
        
        return sum(depths) / len(depths) if depths else 0.0
    
    def _get_python_inheritance_depths(self, file_path: Path) -> List[int]:
        """Get inheritance depths for Python classes."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = ast.parse(content)
            depths = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Count base classes
                    depth = len(node.bases)
                    depths.append(depth)
            
            return depths
        
        except Exception:
            return []
    
    def _calculate_conditional_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of conditional logic."""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                complexity += 1
                # Add complexity for elif chains
                if child.orelse and isinstance(child.orelse[0], ast.If):
                    complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_architecture_score(
        self, coupling: float, cohesion: float, circular_deps: int,
        srp_violations: int, dependency_count: int, module_count: int
    ) -> float:
        """Calculate overall architecture score."""
        
        # Start with perfect score
        score = 10.0
        
        # Penalize high coupling (0-10 scale, 10 is worst)
        score -= (coupling / 10) * 3
        
        # Reward high cohesion (0-10 scale, 10 is best)
        score += (cohesion / 10) * 2 - 1  # Normalize to -1 to +1
        
        # Heavily penalize circular dependencies
        score -= circular_deps * 2
        
        # Penalize SRP violations
        score -= srp_violations * 0.5
        
        # Penalize excessive dependencies relative to modules
        if module_count > 0:
            dependency_ratio = dependency_count / module_count
            if dependency_ratio > 5:  # More than 5 deps per module on average
                score -= (dependency_ratio - 5) * 0.2
        
        return max(0, min(10, score))
