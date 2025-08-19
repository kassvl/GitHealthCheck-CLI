#!/usr/bin/env python3
"""
Comprehensive Backend Test - Test örnek repo üzerinde tüm analyzerleri
"""

import sys
import time
from pathlib import Path

# Add the repo_health_analyzer to path
sys.path.insert(0, str(Path.cwd()))

from repo_health_analyzer.core.analyzers.code_quality_analyzer import CodeQualityAnalyzer
from repo_health_analyzer.core.analyzers.architecture_analyzer import ArchitectureAnalyzer
from repo_health_analyzer.core.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from repo_health_analyzer.core.analyzers.documentation_analyzer import DocumentationAnalyzer
from repo_health_analyzer.core.analyzers.sustainability_analyzer import SustainabilityAnalyzer
from repo_health_analyzer.core.analyzers.test_analyzer import TestAnalyzer
from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig

def test_individual_analyzers():
    """Test her analyzer'ı tek tek örnek repo üzerinde"""
    print('🔍 INDIVIDUAL ANALYZER TESTS')
    print('=' * 80)
    
    # Test repo path
    test_repo_path = Path.cwd() / 'test_sample_repo'
    
    if not test_repo_path.exists():
        print('❌ Test repository not found! Please create it first.')
        return False
    
    print(f'📁 Test Repository: {test_repo_path}')
    print()
    
    # Get Python files from test repo
    python_files = list(test_repo_path.glob('**/*.py'))
    print(f'📊 Found {len(python_files)} Python files to analyze')
    
    config = AnalysisConfig()
    config.max_files = 100
    
    results = {}
    
    # Test 1: Code Quality Analyzer
    print('\n🎯 Testing Code Quality Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        cq_analyzer = CodeQualityAnalyzer(config)
        cq_result = cq_analyzer.analyze(python_files)
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  📊 Overall Score: {cq_result.overall_score:.2f}/10')
        print(f'  📈 Function Length Avg: {cq_result.function_length_avg:.1f}')
        print(f'  📝 Comment Density: {cq_result.comment_density*100:.1f}%')
        print(f'  🏷️  Naming Consistency: {cq_result.naming_consistency*100:.1f}%')
        print(f'  🔄 Duplication Ratio: {cq_result.duplication_ratio*100:.1f}%')
        
        results['code_quality'] = {
            'success': True,
            'duration': duration,
            'score': cq_result.overall_score,
            'function_length': cq_result.function_length_avg
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['code_quality'] = {'success': False, 'error': str(e)}
    
    # Test 2: Code Smell Analyzer
    print('\n🔍 Testing Code Smell Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        smell_analyzer = CodeSmellAnalyzer(config)
        smell_result = smell_analyzer.analyze(python_files)
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  🚨 Total Smells: {smell_result.total_count}')
        print(f'  📊 Severity Score: {smell_result.severity_score:.2f}/10')
        print(f'  🔥 Hotspot Files: {len(smell_result.hotspot_files)}')
        
        if hasattr(smell_result, 'smells_by_type') and smell_result.smells_by_type:
            top_smells = list(smell_result.smells_by_type.keys())[:3]
            print(f'  🔝 Top Smells: {top_smells}')
        
        results['code_smells'] = {
            'success': True,
            'duration': duration,
            'total_smells': smell_result.total_count,
            'hotspots': len(smell_result.hotspot_files)
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['code_smells'] = {'success': False, 'error': str(e)}
    
    # Test 3: Architecture Analyzer
    print('\n🏗️  Testing Architecture Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        arch_analyzer = ArchitectureAnalyzer(config)
        arch_result = arch_analyzer.analyze(python_files)
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  📦 Dependencies: {arch_result.dependency_count}')
        print(f'  🔄 Circular Dependencies: {arch_result.circular_dependencies}')
        print(f'  ⚠️  SRP Violations: {arch_result.srp_violations}')
        print(f'  📊 Overall Score: {arch_result.score:.2f}/10')
        print(f'  🔗 Coupling Score: {arch_result.coupling_score:.2f}/10')
        print(f'  🧩 Cohesion Score: {arch_result.cohesion_score:.2f}/10')
        
        results['architecture'] = {
            'success': True,
            'duration': duration,
            'dependencies': arch_result.dependency_count,
            'violations': arch_result.srp_violations
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['architecture'] = {'success': False, 'error': str(e)}
    
    # Test 4: Documentation Analyzer
    print('\n📚 Testing Documentation Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        doc_analyzer = DocumentationAnalyzer(config)
        doc_result = doc_analyzer.analyze(test_repo_path, python_files)  # source_files parameter
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  📊 Overall Score: {doc_result.score:.2f}/10')
        print(f'  📖 README Quality: {doc_result.readme_quality:.2f}/10')
        print(f'  📝 Docstring Coverage: {doc_result.docstring_coverage*100:.1f}%')
        print(f'  📄 Doc Files: {doc_result.doc_files_count}')
        print(f'  📚 Has Changelog: {doc_result.has_changelog}')
        print(f'  🤝 Has Contributing Guide: {doc_result.has_contributing_guide}')
        
        results['documentation'] = {
            'success': True,
            'duration': duration,
            'coverage': doc_result.score,
            'quality': doc_result.readme_quality
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['documentation'] = {'success': False, 'error': str(e)}
    
    # Test 5: Test Analyzer
    print('\n🧪 Testing Test Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        test_analyzer = TestAnalyzer(config)
        test_result = test_analyzer.analyze(python_files)
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  📊 Coverage Score: {test_result.coverage_score:.2f}/10')
        print(f'  📈 Test to Source Ratio: {test_result.test_to_source_ratio*100:.1f}%')
        print(f'  📁 Test Files: {test_result.test_files_count}')
        print(f'  🧪 Test Success Rate: {test_result.test_success_rate*100:.1f}%')
        print(f'  📈 Has Coverage Report: {test_result.has_coverage_report}')
        
        results['test_analysis'] = {
            'success': True,
            'duration': duration,
            'coverage': test_result.coverage_score,
            'test_files': test_result.test_files_count
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['test_analysis'] = {'success': False, 'error': str(e)}
    
    # Test 6: Sustainability Analyzer
    print('\n🌱 Testing Sustainability Analyzer...')
    print('-' * 50)
    try:
        start_time = time.time()
        sust_analyzer = SustainabilityAnalyzer(config)
        # Mock repo info for sustainability analyzer
        from repo_health_analyzer.models.simple_report import RepositoryInfo
        repo_info = RepositoryInfo(
            name="test_sample_repo",
            path=str(test_repo_path),
            total_commits=1,
            contributors=["test_author"],
            languages={"Python": 1000}
        )
        # Mock commit history for sustainability analyzer
        mock_commits = [{
            'hash': 'abc123',
            'message': 'Initial commit: Sample project with various code quality levels',
            'author': 'test_author',
            'date': '2024-01-01',
            'files_changed': ['src/main.py', 'README.md']
        }]
        sust_result = sust_analyzer.analyze(mock_commits, repo_info, python_files)
        duration = time.time() - start_time
        
        print(f'  ✅ SUCCESS! Duration: {duration:.2f}s')
        print(f'  📊 Sustainability Score: {sust_result.score:.2f}/10')
        print(f'  📈 Activity Trend: {sust_result.activity_trend}')
        print(f'  🚌 Bus Factor: {sust_result.bus_factor}')
        print(f'  🔧 Maintenance Probability: {sust_result.maintenance_probability:.2f}')
        print(f'  👥 Contributor Diversity: {sust_result.contributor_diversity:.2f}')
        
        results['sustainability'] = {
            'success': True,
            'duration': duration,
            'score': sust_result.score,
            'trend': sust_result.activity_trend
        }
        
    except Exception as e:
        print(f'  ❌ FAILED: {e}')
        results['sustainability'] = {'success': False, 'error': str(e)}
    
    return results

def test_full_system_integration():
    """Test tam sistem entegrasyonu"""
    print('\n🚀 FULL SYSTEM INTEGRATION TEST')
    print('=' * 80)
    
    test_repo_path = Path.cwd() / 'test_sample_repo'
    
    config = AnalysisConfig()
    config.max_files = 100
    config.include_patterns = ['*.py', '*.md', '*.txt', '*.json']
    config.exclude_patterns = ['__pycache__/*', '*.pyc', '.git/*']
    
    print(f'📁 Target Repository: {test_repo_path}')
    print(f'📊 Max Files: {config.max_files}')
    print()
    
    try:
        start_time = time.time()
        
        # Initialize full analyzer
        analyzer = RepositoryAnalyzer(test_repo_path, config)
        
        print('🔄 Running full system analysis...')
        report = analyzer.analyze()
        
        duration = time.time() - start_time
        
        print(f'\n✅ FULL SYSTEM ANALYSIS COMPLETED!')
        print(f'⏱️  Total Duration: {duration:.2f} seconds')
        print()
        
        # Display comprehensive results
        print('📊 COMPREHENSIVE RESULTS:')
        print('=' * 50)
        
        # Repository Info
        print(f'📁 Repository: {report.repository.name}')
        print(f'🗂️  Languages: {list(report.repository.languages.keys())}')
        contributors_count = report.repository.contributors if isinstance(report.repository.contributors, int) else len(report.repository.contributors)
        print(f'👥 Contributors: {contributors_count}')
        print()
        
        # All analyzer results
        analyzers_summary = {
            'Code Quality': {
                'score': report.metrics.code_quality.overall_score,
                'complexity': report.metrics.code_quality.cyclomatic_complexity,
                'comment_density': report.metrics.code_quality.comment_density
            },
            'Code Smells': {
                'total': report.metrics.code_smells.total_count,
                'severity': report.metrics.code_smells.severity_score,
                'hotspots': len(report.metrics.code_smells.hotspot_files)
            },
            'Architecture': {
                'score': report.metrics.architecture.score,
                'dependencies': report.metrics.architecture.dependency_count,
                'violations': report.metrics.architecture.srp_violations
            },
            'Documentation': {
                'score': report.metrics.documentation.score,
                'readme_quality': report.metrics.documentation.readme_quality,
                'docstring_coverage': report.metrics.documentation.docstring_coverage
            },
            'Tests': {
                'coverage': report.metrics.tests.coverage_score,
                'files': report.metrics.tests.test_files_count,
                'ratio': report.metrics.tests.test_to_source_ratio
            },
            'Sustainability': {
                'score': report.metrics.sustainability.score,
                'trend': report.metrics.sustainability.activity_trend,
                'bus_factor': report.metrics.sustainability.bus_factor
            }
        }
        
        for analyzer_name, metrics in analyzers_summary.items():
            print(f'{analyzer_name}:')
            for key, value in metrics.items():
                print(f'  • {key}: {value}')
            print()
        
        return True, duration, analyzers_summary
        
    except Exception as e:
        print(f'❌ FULL SYSTEM TEST FAILED: {e}')
        import traceback
        traceback.print_exc()
        return False, 0, {}

def main():
    """Ana test fonksiyonu"""
    print('🎯 COMPREHENSIVE BACKEND TEST SUITE')
    print('=' * 80)
    print(f'🕒 Started at: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # Test 1: Individual Analyzers
    individual_results = test_individual_analyzers()
    
    # Test 2: Full System Integration
    system_success, system_duration, system_results = test_full_system_integration()
    
    # Final Summary
    print('\n🏆 FINAL TEST SUMMARY')
    print('=' * 80)
    
    successful_analyzers = sum(1 for result in individual_results.values() if result.get('success', False))
    total_analyzers = len(individual_results)
    
    print(f'📊 Individual Analyzer Tests: {successful_analyzers}/{total_analyzers} passed')
    print(f'🚀 Full System Integration: {"✅ PASSED" if system_success else "❌ FAILED"}')
    
    if system_success:
        print(f'⏱️  Total System Duration: {system_duration:.2f} seconds')
        
    print()
    print('📈 DETAILED RESULTS:')
    
    for analyzer, result in individual_results.items():
        status = "✅" if result.get('success', False) else "❌"
        duration = result.get('duration', 0)
        print(f'  {status} {analyzer}: {duration:.2f}s')
        
    print()
    
    if successful_analyzers == total_analyzers and system_success:
        print('🎉 ALL TESTS PASSED! Repository Health Analyzer is PRODUCTION READY! 🎉')
        return True
    else:
        print('⚠️  Some tests failed. Please check the errors above.')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
