"""Advanced architecture analyzer using regex patterns and dependency analysis."""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict, Counter
from ...models.simple_report import ArchitectureMetrics, AnalysisConfig

class ArchitectureAnalyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.dependency_patterns = self._initialize_dependency_patterns()
        self.architecture_patterns = self._initialize_architecture_patterns()
        self.design_patterns = self._initialize_design_patterns()
        
    def _initialize_dependency_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize language-specific dependency patterns."""
        return {
            'python': {
                'import': r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
                'from_import': r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import',
                'relative_import': r'^\s*from\s+(\.+[a-zA-Z_][a-zA-Z0-9_\.]*)\s+import',
                'class_def': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(([^)]+)\))?',
                'function_def': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'method_call': r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'instantiation': r'(\w+)\s*\(',
            },
            'javascript': {
                'import': r'from\s+["\']([^"\']+)["\']|import\s+["\']([^"\']+)["\']',
                'require': r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
                'export': r'^\s*export\s+',
                'class_def': r'^\s*class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                'function_def': r'^\s*(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=)',
                'method_call': r'\.([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
            },
            'java': {
                'import': r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
                'package': r'^\s*package\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
                'class_def': r'^\s*(?:public\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'interface_def': r'^\s*(?:public\s+)?interface\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'extends': r'extends\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'implements': r'implements\s+([a-zA-Z_][a-zA-Z0-9_,\s]*)',
            }
        }
    
    def _initialize_architecture_patterns(self) -> Dict[str, str]:
        """Initialize architecture pattern detection."""
        return {
            'mvc_controller': r'(?i)(controller|ctrl)\.py$|class\s+\w*Controller',
            'mvc_model': r'(?i)(model|models)\.py$|class\s+\w*Model',
            'mvc_view': r'(?i)(view|views)\.py$|class\s+\w*View',
            'repository_pattern': r'(?i)repository\.py$|class\s+\w*Repository',
            'service_pattern': r'(?i)service\.py$|class\s+\w*Service',
            'factory_pattern': r'(?i)factory\.py$|class\s+\w*Factory',
            'singleton_pattern': r'class\s+\w+.*?__new__|_instance\s*=\s*None',
            'observer_pattern': r'(?i)observer\.py$|class\s+\w*Observer',
            'strategy_pattern': r'(?i)strategy\.py$|class\s+\w*Strategy',
            'facade_pattern': r'(?i)facade\.py$|class\s+\w*Facade',
            'adapter_pattern': r'(?i)adapter\.py$|class\s+\w*Adapter',
            'decorator_pattern': r'@\w+|class\s+\w*Decorator',
            'builder_pattern': r'(?i)builder\.py$|class\s+\w*Builder',
            'command_pattern': r'(?i)command\.py$|class\s+\w*Command',
            'proxy_pattern': r'(?i)proxy\.py$|class\s+\w*Proxy'
        }
    
    def _initialize_design_patterns(self) -> Dict[str, str]:
        """Initialize SOLID principles and architecture violation patterns."""
        return {
            'solid_srp': r'class\s+\w+.*?def\s+\w+.*?def\s+\w+.*?def\s+\w+',
            'solid_ocp': r'if\s+isinstance\s*\(|if\s+type\s*\(',
            'solid_lsp': r'raise\s+NotImplementedError',
            'solid_isp': r'pass\s*#.*not\s+implemented',
            'solid_dip': r'from\s+\.\w+\s+import\s+\w+',
            'law_of_demeter': r'\.\w+\.\w+\.\w+',
        }
    
    def analyze(self, source_files: List[Path]) -> ArchitectureMetrics:
        """Perform comprehensive architecture analysis."""
        print(f"🏗️  Advanced architecture analysis on {len(source_files)} files...")
        
        # Initialize analysis data structures
        dependency_graph = defaultdict(set)
        module_dependencies = defaultdict(set)
        class_hierarchy = defaultdict(set)
        package_structure = defaultdict(list)
        design_patterns_found: Counter[str] = Counter()
        architecture_violations = []
        
        # Language distribution
        language_stats: Counter[str] = Counter()
        
        # Process each file for architecture analysis
        for i, file_path in enumerate(source_files):
            if i % 30 == 0:
                print(f"  📁 Analyzing {i+1}/{len(source_files)}: {file_path.name}")
            
            try:
                file_analysis = self._analyze_file_architecture(file_path)
                if file_analysis:
                    # Update dependency graph
                    module_name = self._get_module_name(file_path)
                    dependency_graph[module_name].update(file_analysis['dependencies'])
                    module_dependencies[module_name] = file_analysis['dependencies']
                    
                    # Update class hierarchy
                    for class_name, parent_classes in file_analysis['inheritance'].items():
                        class_hierarchy[class_name].update(parent_classes)
                    
                    # Update package structure
                    package_name = self._get_package_name(file_path)
                    package_structure[package_name].append(module_name)
                    
                    # Count design patterns
                    design_patterns_found.update(file_analysis['patterns'])
                    
                    # Track violations
                    architecture_violations.extend(file_analysis['violations'])
                    
                    # Language stats
                    language_stats[file_analysis['language']] += 1
                    
            except Exception as e:
                print(f"  ⚠️  Error analyzing {file_path.name}: {str(e)[:50]}...")
                continue
        
        # Calculate architecture metrics
        metrics = self._calculate_architecture_metrics(
            dependency_graph, module_dependencies, class_hierarchy,
            package_structure, design_patterns_found, architecture_violations,
            language_stats, len(source_files)
        )
        
        print(f"  ✅ Architecture analysis complete!")
        print(f"     📊 Overall Score: {metrics['overall_score']:.1f}/10")
        print(f"     🔗 Dependencies: {metrics['dependency_count']}")
        print(f"     🔄 Circular Deps: {metrics['circular_dependencies']}")
        print(f"     🎯 Design Patterns: {len(design_patterns_found)}")
        
        return ArchitectureMetrics(
            score=round(metrics['overall_score'], 1),
            dependency_count=int(metrics['dependency_count']),
            circular_dependencies=int(metrics['circular_dependencies']),
            coupling_score=round(metrics['coupling_score'], 1),
            cohesion_score=round(metrics['cohesion_score'], 1),
            srp_violations=int(metrics['srp_violations']),
            module_count=int(metrics['module_count']),
            depth_of_inheritance=round(metrics['depth_of_inheritance'], 1)
        )
    
    def _analyze_file_architecture(self, file_path: Path) -> Dict[str, Any]:
        """Analyze architecture aspects of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return {}
        
        if not content.strip():
            return {}
        
        # Detect language
        language = self._detect_language(file_path.suffix.lower())
        patterns = self.dependency_patterns.get(language, {})
        
        # Initialize analysis results
        analysis = {
            'language': language,
            'dependencies': set(),
            'inheritance': {},
            'patterns': [],
            'violations': [],
            'complexity_indicators': []
        }
        
        # Extract dependencies
        analysis['dependencies'] = self._extract_dependencies(content, patterns)
        
        # Extract inheritance relationships
        analysis['inheritance'] = self._extract_inheritance(content, patterns, language)
        
        # Detect design patterns
        analysis['patterns'] = self._detect_design_patterns(content, file_path)
        
        # Detect architecture violations  
        violations_result = self._detect_architecture_violations(content, file_path)
        analysis['violations'] = [v['type'] for v in violations_result] if violations_result else []
        
        # Analyze complexity indicators
        analysis['complexity_indicators'] = self._analyze_complexity_indicators(content, patterns)
        
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
    
    def _extract_dependencies(self, content: str, patterns: Dict[str, str]) -> Set[str]:
        """Extract module dependencies using regex patterns."""
        dependencies = set()
        
        # Standard imports
        if 'import' in patterns:
            imports = re.findall(patterns['import'], content, re.MULTILINE)
            dependencies.update(imports)
        
        # From imports
        if 'from_import' in patterns:
            from_imports = re.findall(patterns['from_import'], content, re.MULTILINE)
            dependencies.update(from_imports)
        
        # Relative imports
        if 'relative_import' in patterns:
            rel_imports = re.findall(patterns['relative_import'], content, re.MULTILINE)
            dependencies.update(rel_imports)
        
        # Require statements (JavaScript)
        if 'require' in patterns:
            requires = re.findall(patterns['require'], content, re.MULTILINE)
            dependencies.update(requires)
        
        # Clean up dependencies (remove built-ins and standard library)
        cleaned_deps = set()
        for dep in dependencies:
            # Handle tuples from regex groups
            if isinstance(dep, tuple):
                for group in dep:
                    if group and not self._is_builtin_module(group):
                        # Keep full name for Java packages, root for others
                        if '.' in group and (group.startswith('com.') or group.startswith('org.')):
                            cleaned_deps.add(group)  # Keep full Java package name
                        else:
                            cleaned_deps.add(group.split('.')[0])  # Get root module
            else:
                if dep and not self._is_builtin_module(dep):
                    # Keep full name for Java packages, root for others
                    if '.' in dep and (dep.startswith('com.') or dep.startswith('org.')):
                        cleaned_deps.add(dep)  # Keep full Java package name
                    else:
                        cleaned_deps.add(dep.split('.')[0])  # Get root module
        
        return cleaned_deps
    
    def _extract_inheritance(self, content: str, patterns: Dict[str, str], language: str) -> Dict[str, List[str]]:
        """Extract class inheritance relationships."""
        inheritance = {}
        
        if language == 'python':
            # Python class inheritance
            class_matches = re.finditer(patterns.get('class_def', ''), content, re.MULTILINE)
            for match in class_matches:
                if len(match.groups()) >= 2 and match.group(2):
                    class_name = match.group(1)
                    parent_classes = [p.strip() for p in match.group(2).split(',')]
                    inheritance[class_name] = parent_classes
        
        return inheritance
    
    def _detect_design_patterns(self, content: str, file_path: Path) -> List[str]:
        """Detect design patterns in the code."""
        patterns_found = []
        
        for pattern_name, pattern_regex in self.architecture_patterns.items():
            # Check file name patterns
            if re.search(pattern_regex, str(file_path)):
                patterns_found.append(pattern_name)
            # Check content patterns
            elif re.search(pattern_regex, content, re.MULTILINE | re.IGNORECASE):
                patterns_found.append(pattern_name)
        
        return patterns_found
    
    def _detect_architecture_violations(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect architecture and design principle violations."""
        violations = []
        
        for principle, pattern in self.design_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                violations.append({
                    'type': principle,
                    'file': str(file_path),
                    'line': content[:match.start()].count('\n') + 1,
                    'description': self._get_violation_description(principle)
                })
        
        # Check for god classes (classes with too many methods)
        class_matches = re.finditer(r'class\s+(\w+).*?(?=class|\Z)', content, re.DOTALL)
        for match in class_matches:
            class_content = match.group(0)
            method_count = len(re.findall(r'def\s+\w+', class_content))
            if method_count > 20:  # Threshold for god class
                violations.append({
                    'type': 'god_class',
                    'file': str(file_path),
                    'class': match.group(1),
                    'method_count': method_count,
                    'description': f'Class has {method_count} methods (threshold: 20)'
                })
        
        return violations
    
    def _analyze_complexity_indicators(self, content: str, patterns: Dict[str, str]) -> Dict[str, int]:
        """Analyze architectural complexity indicators."""
        indicators = {
            'class_count': len(re.findall(patterns.get('class_def', r'class\s+\w+'), content, re.MULTILINE)),
            'function_count': len(re.findall(patterns.get('function_def', r'def\s+\w+'), content, re.MULTILINE)),
            'method_calls': len(re.findall(patterns.get('method_call', r'\.\w+\s*\('), content)),
            'instantiations': len(re.findall(patterns.get('instantiation', r'\w+\s*\('), content))
        }
        
        return indicators
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        return file_path.stem
    
    def _get_package_name(self, file_path: Path) -> str:
        """Get package name from file path."""
        return file_path.parent.name
    
    def _is_builtin_module(self, module_name: str) -> bool:
        """Check if module is a built-in or standard library module."""
        builtin_modules = {
            # Python built-ins (only core built-ins, not standard library)
            'os', 'sys', 're', 'json', 'datetime', 'collections', 'itertools',
            'functools', 'math', 'random', 'string',
            # JavaScript built-ins (only core Node.js modules)
            'path', 'util', 'crypto', 'http', 'https', 'url', 'fs',
            # Java built-ins
            'java.util', 'java.io', 'java.lang', 'java.net'
        }
        
        # Exact match for short names, prefix match for long names
        return any(
            module_name == builtin or 
            (len(builtin) > 3 and module_name.startswith(builtin + '.'))
            for builtin in builtin_modules
        )
    
    def _get_violation_description(self, violation_type: str) -> str:
        """Get human-readable description for violation type."""
        descriptions = {
            'solid_srp': 'Single Responsibility Principle violation - class has multiple responsibilities',
            'solid_ocp': 'Open/Closed Principle violation - using type checking instead of polymorphism',
            'solid_lsp': 'Liskov Substitution Principle violation - subclass cannot replace parent',
            'solid_isp': 'Interface Segregation Principle violation - forcing implementation of unused methods',
            'solid_dip': 'Dependency Inversion Principle violation - depending on concrete implementations',
            'law_of_demeter': 'Law of Demeter violation - accessing distant objects through chain of calls',
            'god_class': 'God Class anti-pattern - class is too large and complex'
        }
        
        return descriptions.get(violation_type, f'Architecture violation: {violation_type}')
    
    def _calculate_architecture_metrics(self, dependency_graph: Dict, module_dependencies: Dict,
                                      class_hierarchy: Dict, package_structure: Dict,
                                      design_patterns: Counter, violations: List,
                                      language_stats: Counter, total_files: int) -> Dict[str, float]:
        """Calculate comprehensive architecture metrics."""
        
        # Dependency metrics
        total_dependencies = sum(len(deps) for deps in dependency_graph.values())
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        
        # Coupling metrics (fan-out and fan-in)
        fan_out = {module: len(deps) for module, deps in dependency_graph.items()}
        fan_in: Dict[str, int] = defaultdict(int)
        for module, deps in dependency_graph.items():
            for dep in deps:
                fan_in[dep] += 1
        
        avg_fan_out = sum(fan_out.values()) / len(fan_out) if fan_out else 0
        avg_fan_in = sum(fan_in.values()) / len(fan_in) if fan_in else 0
        coupling_score = max(0, 10 - (avg_fan_out + avg_fan_in) / 4)
        
        # Cohesion metrics
        package_cohesion_scores = []
        for package, modules in package_structure.items():
            if len(modules) > 1:
                internal_deps = 0
                external_deps = 0
                for module in modules:
                    for dep in module_dependencies.get(module, []):
                        if dep in modules:
                            internal_deps += 1
                        else:
                            external_deps += 1
                
                if internal_deps + external_deps > 0:
                    cohesion = internal_deps / (internal_deps + external_deps)
                    package_cohesion_scores.append(cohesion)
        
        avg_cohesion = sum(package_cohesion_scores) / len(package_cohesion_scores) if package_cohesion_scores else 0.5
        cohesion_score = avg_cohesion * 10
        
        # Inheritance depth
        avg_depth = 1.5  # Default value
        if class_hierarchy:
            depths = []
            for class_name in class_hierarchy:
                depth = self._calculate_inheritance_depth(class_name, class_hierarchy, set())
                depths.append(depth)
            avg_depth = sum(depths) / len(depths) if depths else 1.5
        
        # SOLID violations
        srp_violations = len([v for v in violations if v['type'] == 'solid_srp'])
        
        # Overall architecture score
        violation_penalty = min(5, len(violations) * 0.1)
        complexity_penalty = min(2, (total_dependencies / total_files - 2) * 0.5) if total_files > 0 else 0
        pattern_bonus = min(1, len(design_patterns) * 0.1)
        
        overall_score = max(0, 8.0 - violation_penalty - complexity_penalty + pattern_bonus)
        
        return {
            'overall_score': overall_score,
            'dependency_count': total_dependencies,
            'circular_dependencies': len(circular_deps),
            'coupling_score': coupling_score,
            'cohesion_score': cohesion_score,
            'srp_violations': srp_violations,
            'module_count': len(dependency_graph),
            'depth_of_inheritance': avg_depth
        }
    
    def _detect_circular_dependencies(self, dependency_graph: Dict) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node) if node in path else 0
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in dependency_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _calculate_inheritance_depth(self, class_name: str, hierarchy: Dict, visited: Set) -> int:
        """Calculate inheritance depth for a class."""
        # Check for circular reference using simple cycle detection
        def has_cycle(start_class, current_class, path):
            if current_class in path:
                return True
            
            parents = hierarchy.get(current_class, [])
            if not parents:
                return False
                
            path.add(current_class)
            for parent in parents:
                if has_cycle(start_class, parent, path):
                    return True
            path.remove(current_class)
            return False
        
        # If circular reference exists, return 0
        if has_cycle(class_name, class_name, set()):
            return 0
            
        # Otherwise calculate normal depth
        return self._calculate_depth_helper(class_name, hierarchy, set())
    
    def _calculate_depth_helper(self, class_name: str, hierarchy: Dict, current_path: Set) -> int:
        """Helper method for calculating inheritance depth."""
        parents = hierarchy.get(class_name, [])
        if not parents:
            return 1  # Base case - no parents
        
        max_depth = 0
        for parent in parents:
            parent_depth = self._calculate_depth_helper(parent, hierarchy, current_path)
            max_depth = max(max_depth, parent_depth)
        
        return max_depth + 1

    def _generate_architecture_insights(self, dependency_graph: Dict[str, Set[str]], 
                                       design_patterns: Dict[str, int],
                                       violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate architecture insights and recommendations."""
        insights: Dict[str, Any] = {
            'recommendations': [],
            'design_patterns_used': {},
            'top_violations': [],
            'dependency_hotspots': []
        }
        
        # Design patterns used
        for pattern, count in design_patterns.items():
            if count > 0:
                insights['design_patterns_used'][pattern] = count
        
        # Top violations
        violation_counts: Dict[str, int] = {}
        for violation in violations:
            violation_type = violation.get('type', 'unknown')
            violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1
        
        insights['top_violations'] = [
            {'type': vtype, 'count': count}
            for vtype, count in sorted(violation_counts.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Dependency hotspots (modules with most dependencies)
        dependency_counts = {
            module: len(deps) for module, deps in dependency_graph.items()
        }
        
        insights['dependency_hotspots'] = [
            {'module': module, 'dependency_count': count}
            for module, count in sorted(dependency_counts.items(), 
                                      key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Generate recommendations
        recommendations = []
        
        if violation_counts.get('solid_srp', 0) > 2:
            recommendations.append({
                'type': 'refactoring',
                'priority': 'high',
                'message': 'Consider splitting classes with multiple responsibilities (SRP violations)'
            })
        
        if violation_counts.get('solid_ocp', 0) > 1:
            recommendations.append({
                'type': 'design',
                'priority': 'medium',
                'message': 'Use abstraction and interfaces to follow Open/Closed Principle'
            })
        
        max_dependencies = max(dependency_counts.values()) if dependency_counts else 0
        if max_dependencies > 5:
            recommendations.append({
                'type': 'architecture',
                'priority': 'medium',
                'message': 'Consider reducing module dependencies to improve maintainability'
            })
        
        if not design_patterns:
            recommendations.append({
                'type': 'design',
                'priority': 'low',
                'message': 'Consider using design patterns to improve code structure'
            })
        
        insights['recommendations'] = recommendations
        return insights
