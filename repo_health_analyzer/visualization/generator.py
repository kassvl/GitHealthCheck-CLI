"""
Visualization generator for health reports.

Creates heatmaps, dependency graphs, and other visualizations
for repository health analysis results.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

from ..models.report import HealthReport


class VisualizationGenerator:
    """
    Generator for various visualizations of repository health data.
    
    Creates dependency graphs, code smell heatmaps, and metric charts.
    """
    
    def __init__(self):
        self.output_dir = Path.cwd()
    
    def generate_all(self, report: HealthReport, repo_path: Path) -> None:
        """
        Generate all available visualizations for the health report.
        
        Args:
            report: Health report to visualize
            repo_path: Repository path for context
        """
        # Generate dependency graph
        if HAS_GRAPHVIZ:
            self.generate_dependency_graph(report)
        
        # Generate code smell heatmap data
        self.generate_smell_heatmap_data(report)
        
        # Generate metrics summary chart data
        self.generate_metrics_chart_data(report)
        
        # Generate sustainability trend data
        self.generate_sustainability_data(report)
    
    def generate_dependency_graph(self, report: HealthReport) -> None:
        """Generate dependency graph visualization."""
        if not HAS_GRAPHVIZ:
            print("Warning: graphviz not available, skipping dependency graph")
            return
        
        try:
            dot = graphviz.Digraph(comment='Repository Dependencies')
            dot.attr(rankdir='TB', size='12,8')
            dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
            
            # Add nodes for main modules (simplified)
            modules = self._extract_main_modules(report)
            
            for module in modules:
                dot.node(module['name'], module['name'])
            
            # Add edges for dependencies (simplified)
            for module in modules:
                for dep in module.get('dependencies', []):
                    if dep in [m['name'] for m in modules]:
                        dot.edge(module['name'], dep)
            
            # Save as SVG
            output_path = self.output_dir / 'dependency_graph'
            dot.render(output_path, format='svg', cleanup=True)
            
            print(f"Dependency graph saved to: {output_path}.svg")
        
        except Exception as e:
            print(f"Warning: Could not generate dependency graph: {e}")
    
    def generate_smell_heatmap_data(self, report: HealthReport) -> None:
        """Generate code smell heatmap data as JSON."""
        heatmap_data = {
            'title': 'Code Smell Heatmap',
            'description': 'Visualization of code smells across repository files',
            'data': []
        }
        
        # Group smells by file
        smells_by_file = {}
        for smell in report.metrics.code_smells.smells:
            file_path = smell.file_path
            if file_path not in smells_by_file:
                smells_by_file[file_path] = []
            smells_by_file[file_path].append({
                'type': smell.type,
                'line': smell.line_number,
                'severity': smell.severity,
                'description': smell.description
            })
        
        # Convert to heatmap format
        for file_path, smells in smells_by_file.items():
            total_severity = sum(smell['severity'] for smell in smells)
            heatmap_data['data'].append({
                'file': file_path,
                'smell_count': len(smells),
                'total_severity': round(total_severity, 1),
                'avg_severity': round(total_severity / len(smells), 1),
                'smells': smells
            })
        
        # Sort by severity
        heatmap_data['data'].sort(key=lambda x: x['total_severity'], reverse=True)
        
        # Save as JSON
        output_path = self.output_dir / 'smell_heatmap.json'
        with open(output_path, 'w') as f:
            json.dump(heatmap_data, f, indent=2)
        
        print(f"Code smell heatmap data saved to: {output_path}")
    
    def generate_metrics_chart_data(self, report: HealthReport) -> None:
        """Generate metrics chart data as JSON."""
        metrics_data = {
            'title': 'Repository Health Metrics',
            'overall_score': report.metrics.overall_score,
            'categories': [
                {
                    'name': 'Code Quality',
                    'score': report.metrics.code_quality.overall_score,
                    'details': {
                        'complexity': report.metrics.code_quality.cyclomatic_complexity,
                        'function_length': report.metrics.code_quality.function_length_avg,
                        'comment_density': report.metrics.code_quality.comment_density,
                        'naming_consistency': report.metrics.code_quality.naming_consistency
                    }
                },
                {
                    'name': 'Architecture',
                    'score': report.metrics.architecture.score,
                    'details': {
                        'coupling': report.metrics.architecture.coupling_score,
                        'cohesion': report.metrics.architecture.cohesion_score,
                        'circular_deps': report.metrics.architecture.circular_dependencies,
                        'srp_violations': report.metrics.architecture.srp_violations
                    }
                },
                {
                    'name': 'Code Smells',
                    'score': 10 - min(report.metrics.code_smells.severity_score, 10),
                    'details': {
                        'total_count': report.metrics.code_smells.total_count,
                        'severity': report.metrics.code_smells.severity_score,
                        'by_type': report.metrics.code_smells.smells_by_type
                    }
                },
                {
                    'name': 'Tests',
                    'score': report.metrics.tests.coverage_score,
                    'details': {
                        'test_files': report.metrics.tests.test_files_count,
                        'test_ratio': report.metrics.tests.test_to_source_ratio,
                        'success_rate': report.metrics.tests.test_success_rate
                    }
                },
                {
                    'name': 'Documentation',
                    'score': report.metrics.documentation.score,
                    'details': {
                        'readme_quality': report.metrics.documentation.readme_quality,
                        'docstring_coverage': report.metrics.documentation.docstring_coverage,
                        'has_changelog': report.metrics.documentation.has_changelog
                    }
                },
                {
                    'name': 'Sustainability',
                    'score': report.metrics.sustainability.score,
                    'details': {
                        'maintenance_prob': report.metrics.sustainability.maintenance_probability,
                        'activity_trend': report.metrics.sustainability.activity_trend,
                        'bus_factor': report.metrics.sustainability.bus_factor
                    }
                }
            ]
        }
        
        # Save as JSON
        output_path = self.output_dir / 'metrics_chart.json'
        with open(output_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        print(f"Metrics chart data saved to: {output_path}")
    
    def generate_sustainability_data(self, report: HealthReport) -> None:
        """Generate sustainability trend visualization data."""
        sustainability_data = {
            'title': 'Repository Sustainability Analysis',
            'overall_score': report.metrics.sustainability.score,
            'maintenance_probability': report.metrics.sustainability.maintenance_probability,
            'activity_trend': report.metrics.sustainability.activity_trend,
            'metrics': {
                'bus_factor': {
                    'value': report.metrics.sustainability.bus_factor,
                    'description': 'Number of key contributors',
                    'recommendation': 'Aim for 3+ key contributors'
                },
                'recent_activity': {
                    'value': report.metrics.sustainability.recent_activity_score,
                    'description': 'Recent development activity',
                    'recommendation': 'Maintain regular commits'
                },
                'contributor_diversity': {
                    'value': report.metrics.sustainability.contributor_diversity,
                    'description': 'Distribution of contributions',
                    'recommendation': 'Encourage diverse contributions'
                },
                'commit_frequency': {
                    'value': report.metrics.sustainability.commit_frequency_score,
                    'description': 'Consistency of development',
                    'recommendation': 'Maintain steady development pace'
                }
            },
            'risk_factors': self._identify_sustainability_risks(report)
        }
        
        # Save as JSON
        output_path = self.output_dir / 'sustainability_analysis.json'
        with open(output_path, 'w') as f:
            json.dump(sustainability_data, f, indent=2)
        
        print(f"Sustainability analysis saved to: {output_path}")
    
    def _extract_main_modules(self, report: HealthReport) -> List[Dict[str, Any]]:
        """Extract main modules for dependency graph (simplified)."""
        # This is a simplified version - in practice, you'd extract from actual dependency analysis
        modules = [
            {'name': 'core', 'dependencies': ['utils', 'models']},
            {'name': 'cli', 'dependencies': ['core']},
            {'name': 'models', 'dependencies': []},
            {'name': 'utils', 'dependencies': ['models']},
            {'name': 'tests', 'dependencies': ['core', 'models']}
        ]
        
        return modules
    
    def _identify_sustainability_risks(self, report: HealthReport) -> List[Dict[str, str]]:
        """Identify key sustainability risk factors."""
        risks = []
        
        sustainability = report.metrics.sustainability
        
        if sustainability.bus_factor < 2:
            risks.append({
                'type': 'Bus Factor Risk',
                'description': 'Too few key contributors',
                'severity': 'high'
            })
        
        if sustainability.activity_trend == 'declining':
            risks.append({
                'type': 'Activity Decline',
                'description': 'Recent development activity is decreasing',
                'severity': 'medium'
            })
        
        if sustainability.contributor_diversity < 0.3:
            risks.append({
                'type': 'Low Contributor Diversity',
                'description': 'Contributions concentrated among few people',
                'severity': 'medium'
            })
        
        if sustainability.recent_activity_score < 3:
            risks.append({
                'type': 'Low Recent Activity',
                'description': 'Very little recent development activity',
                'severity': 'high'
            })
        
        return risks
