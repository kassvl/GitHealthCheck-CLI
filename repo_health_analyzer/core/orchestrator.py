"""
Analysis orchestrator for coordinating different analysis modules.

Separates the orchestration logic from the main analyzer to improve modularity.
"""

from typing import Dict, Any, List, Set, Optional
from pathlib import Path

from ..models.simple_report import OverallMetrics, Recommendation, Priority


class AnalysisOrchestrator:
    """
    Orchestrates the execution of different analysis modules.
    
    Handles the coordination and sequencing of analysis steps,
    keeping the main analyzer focused on data processing.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.analysis_steps: List[Dict[str, Any]] = []
        self.api_instance = None
    
    def register_step(self, name: str, analyzer, method_name: str, dependencies: Optional[List[str]] = None):
        """Register an analysis step with its dependencies."""
        self.analysis_steps.append({
            'name': name,
            'analyzer': analyzer,
            'method': method_name,
            'dependencies': dependencies or []
        })
    
    def execute_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all registered analysis steps in the correct order.
        
        Args:
            context: Analysis context containing repository info and shared data
            
        Returns:
            Dict containing results from all analysis steps
        """
        results: Dict[str, Any] = {}
        completed_steps: Set[str] = set()
        
        # Simple dependency resolution - execute steps when dependencies are met
        total_steps = len(self.analysis_steps)
        
        while len(completed_steps) < total_steps:
            for step in self.analysis_steps:
                if step['name'] in completed_steps:
                    continue
                
                # Check if all dependencies are completed
                if all(dep in completed_steps for dep in step['dependencies']):
                    # Update progress
                    progress = (len(completed_steps) / total_steps) * 100
                    if self.api_instance:
                        step_names = {
                            'git_parsing': 'Parsing Git repository...',
                            'source_files': 'Scanning source files...',
                            'commit_history': 'Analyzing commit history...',
                            'code_quality': 'Evaluating code quality...',
                            'code_smells': 'Detecting code smells...',
                            'architecture': 'Analyzing architecture...',
                            'tests': 'Checking test coverage...',
                            'documentation': 'Evaluating documentation...',
                            'sustainability': 'Computing sustainability...'
                        }
                        step_display = step_names.get(step['name'], step['name'])
                        self.api_instance.current_step = step_display
                        self.api_instance.current_progress = progress
                    
                    # Execute the step
                    analyzer = step['analyzer']
                    method = getattr(analyzer, step['method'])
                    
                    if self.verbose:
                        print(f"Executing: {step['name']}")
                    
                    # Pass relevant context to the method
                    result = self._execute_step_method(method, context, results)
                    results[step['name']] = result
                    completed_steps.add(step['name'])
                    
                    # Debug: print what we got from this step
                    if self.verbose:
                        print(f"Step '{step['name']}' returned: {type(result)}")
                        if step['name'] == 'source_files' and hasattr(result, '__len__'):
                            print(f"  Source files count: {len(result)}")
                    
                    break
            else:
                # No step could be executed - circular dependency or missing dependency
                remaining = [s['name'] for s in self.analysis_steps if s['name'] not in completed_steps]
                raise RuntimeError(f"Cannot resolve dependencies for steps: {remaining}")
        
        return results
    
    def _execute_step_method(self, method, context: Dict[str, Any], results: Dict[str, Any]):
        """Execute a single analysis step method with appropriate parameters."""
        import inspect
        
        # Get method signature to determine what parameters to pass
        sig = inspect.signature(method)
        kwargs = {}
        
        # Map common parameter names to context values - ensure source_files is always a list
        source_files_result = results.get('source_files', context.get('source_files'))
        if source_files_result is not None and not isinstance(source_files_result, list):
            source_files_result = [source_files_result] if source_files_result else []
        # Cap number of files for responsiveness on huge repos
        if source_files_result and isinstance(source_files_result, list):
            try:
                max_files = 1000  # 1000 dosya test
                if len(source_files_result) > max_files:
                    if self.verbose:
                        print(f"Limiting source_files from {len(source_files_result)} to {max_files} for responsiveness")
                    source_files_result = source_files_result[:max_files]
            except Exception:
                pass
        
        # Debug print to see what we're passing
        if self.verbose and 'source_files' in sig.parameters:
            print(f"DEBUG: source_files_result = {type(source_files_result)}, len={len(source_files_result) if source_files_result else 'None'}")
        
        param_mapping = {
            'repo_path': context.get('repo_path'),
            'source_files': source_files_result,
            'commit_history': results.get('commit_history', context.get('commit_history')),
            'repo_info': results.get('git_parsing', context.get('repo_info'))
        }
        
        for param_name in sig.parameters:
            if param_name in param_mapping and param_mapping[param_name] is not None:
                kwargs[param_name] = param_mapping[param_name]
            elif param_name in context:
                kwargs[param_name] = context[param_name]
            elif param_name in results:
                kwargs[param_name] = results[param_name]
        
        # Call method with appropriate parameters
        if kwargs:
            return method(**kwargs)
        else:
            return method()


class MetricsCalculator:
    """
    Handles calculation of overall metrics and recommendations.
    
    Separated from the main analyzer to follow single responsibility principle.
    """
    
    @staticmethod
    def calculate_overall_metrics(
        code_quality,
        architecture,
        code_smells,
        tests,
        docs,
        sustainability
    ) -> OverallMetrics:
        """Calculate overall score from individual metric scores."""
        
        # Weighted average of all scores
        weights = {
            'code_quality': 0.25,
            'architecture': 0.20,
            'code_smells': 0.15,  # Inverted - fewer smells = higher score
            'tests': 0.20,
            'docs': 0.10,
            'sustainability': 0.10
        }
        
        # Handle None values gracefully
        smell_score = max(0, 10 - getattr(code_smells, 'severity_score', 0)) if code_smells else 10
        
        overall_score = (
            getattr(code_quality, 'overall_score', 0) * weights['code_quality'] +
            getattr(architecture, 'score', 0) * weights['architecture'] +
            smell_score * weights['code_smells'] +
            getattr(tests, 'coverage_score', 0) * weights['tests'] +
            getattr(docs, 'score', 0) * weights['docs'] +
            getattr(sustainability, 'score', 0) * weights['sustainability']
        )
        
        return OverallMetrics(
            overall_score=round(overall_score, 1),
            code_quality=code_quality,
            architecture=architecture,
            code_smells=code_smells,
            tests=tests,
            documentation=docs,
            sustainability=sustainability
        )
    
    @staticmethod
    def generate_recommendations(metrics: OverallMetrics) -> List[Recommendation]:
        """Generate actionable recommendations based on analysis results."""
        
        recommendations = []
        
        # Code quality recommendations
        if hasattr(metrics.code_quality, 'overall_score') and getattr(metrics.code_quality, 'overall_score', 10) < 6:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Code Quality",
                description="Reduce cyclomatic complexity in complex functions",
                impact="Improves maintainability and reduces bugs",
                effort="medium"
            ))
        
        if hasattr(metrics.code_quality, 'comment_density') and getattr(metrics.code_quality, 'comment_density', 1.0) < 0.1:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Code Quality",
                description="Increase code documentation and comments",
                impact="Better code understanding for team members",
                effort="low"
            ))
        
        # Architecture recommendations
        if hasattr(metrics.architecture, 'circular_dependencies') and getattr(metrics.architecture, 'circular_dependencies', 0) > 0:
            recommendations.append(Recommendation(
                priority=Priority.CRITICAL,
                category="Architecture",
                description="Resolve circular dependencies between modules",
                impact="Prevents build issues and improves modularity",
                effort="high"
            ))
        
        if metrics.architecture.coupling_score > 7:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Architecture",
                description="Reduce coupling between modules",
                impact="Improves testability and maintainability",
                effort="medium"
            ))
        
        # Code smell recommendations
        if metrics.code_smells.total_count > 50:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Code Smells",
                description="Address high-priority code smells in hotspot files",
                impact="Reduces technical debt and improves code quality",
                effort="medium",
                files_affected=metrics.code_smells.hotspot_files[:5]
            ))
        
        # Test recommendations
        if hasattr(metrics.tests, 'coverage_score') and getattr(metrics.tests, 'coverage_score', 10) < 7:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Testing",
                description="Increase test coverage, especially for critical modules",
                impact="Reduces bugs and improves confidence in changes",
                effort="high"
            ))
        
        if hasattr(metrics.tests, 'test_to_source_ratio') and getattr(metrics.tests, 'test_to_source_ratio', 1.0) < 0.3:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Testing",
                description="Add more comprehensive test cases",
                impact="Better validation of functionality",
                effort="medium"
            ))
        
        # Documentation recommendations
        if hasattr(metrics.documentation, 'score') and getattr(metrics.documentation, 'score', 10) < 6:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Documentation",
                description="Improve API documentation and code comments",
                impact="Better onboarding and maintenance",
                effort="low"
            ))
        
        if not metrics.documentation.has_contributing_guide:
            recommendations.append(Recommendation(
                priority=Priority.LOW,
                category="Documentation",
                description="Add CONTRIBUTING.md guide for new contributors",
                impact="Easier contribution process",
                effort="low"
            ))
        
        # Sustainability recommendations
        if hasattr(metrics.sustainability, 'score') and getattr(metrics.sustainability, 'score', 10) < 6:
            recommendations.append(Recommendation(
                priority=Priority.MEDIUM,
                category="Sustainability",
                description="Increase commit frequency and contributor diversity",
                impact="Ensures long-term project viability",
                effort="high"
            ))
        
        if hasattr(metrics.sustainability, 'bus_factor') and getattr(metrics.sustainability, 'bus_factor', 10) < 3:
            recommendations.append(Recommendation(
                priority=Priority.HIGH,
                category="Sustainability",
                description="Reduce bus factor by spreading knowledge across team",
                impact="Reduces project risk",
                effort="medium"
            ))
        
        # Sort by priority
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        return recommendations
