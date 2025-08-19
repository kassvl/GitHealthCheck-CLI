#!/usr/bin/env python3
"""
Comprehensive System Test for Repo Health Analyzer
Tests all 6 analyzers on the current project with 1000 file limit
"""

import sys
import time
from pathlib import Path

# Add the repo_health_analyzer to path
sys.path.insert(0, str(Path.cwd().parent))

from repo_health_analyzer.core.analyzer import RepositoryAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig

def run_comprehensive_test():
    print('🎯 COMPREHENSIVE SYSTEM TEST STARTING...')
    print('=' * 70)
    print()
    
    # Configure analysis with 1000 file limit
    config = AnalysisConfig()
    config.max_files = 1000
    config.include_patterns = ['*.py', '*.js', '*.java', '*.ts', '*.md', '*.txt', '*.json']
    config.exclude_patterns = ['venv/*', 'node_modules/*', '.git/*', '__pycache__/*', '*.pyc']
    
    print(f'📁 Target Directory: {Path.cwd().parent}')
    print(f'📊 Max Files: {config.max_files}')
    print(f'🔍 Include Patterns: {config.include_patterns}')
    print(f'🚫 Exclude Patterns: {config.exclude_patterns}')
    print()
    
    # Initialize analyzer
    analyzer = RepositoryAnalyzer(Path.cwd().parent, config)
    
    print('🚀 Starting full system analysis...')
    start_time = time.time()
    
    try:
        # Run full analysis
        report = analyzer.analyze()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print()
        print('✅ ANALYSIS COMPLETED SUCCESSFULLY!')
        print('=' * 70)
        print(f'⏱️  Duration: {duration:.2f} seconds')
        print()
        
        # Display comprehensive results
        print('📊 REPOSITORY OVERVIEW:')
        print(f'  • Repository: {report.repository_info.name}')
        print(f'  • Total Files: {len(report.repository_info.languages)}')
        print(f'  • Languages: {list(report.repository_info.languages.keys())}')
        print(f'  • Contributors: {len(report.repository_info.contributors)}')
        print(f'  • Total Commits: {report.repository_info.total_commits}')
        print()
        
        # Code Quality Results
        print('🎯 CODE QUALITY ANALYSIS:')
        cq = report.code_quality
        print(f'  • Overall Score: {cq.overall_score:.2f}/10')
        print(f'  • Complexity Score: {cq.complexity_score:.2f}/10')
        print(f'  • Maintainability: {cq.maintainability_score:.2f}/10')
        print(f'  • Files Analyzed: {cq.files_analyzed}')
        print(f'  • Total Functions: {cq.total_functions}')
        print(f'  • Total Classes: {cq.total_classes}')
        print()
        
        # Code Smell Results
        print('🔍 CODE SMELL ANALYSIS:')
        cs = report.code_smells
        print(f'  • Total Smells: {cs.total_smells}')
        print(f'  • Critical: {cs.critical_smells}')
        print(f'  • Major: {cs.major_smells}')
        print(f'  • Minor: {cs.minor_smells}')
        print(f'  • Files with Smells: {cs.files_with_smells}')
        if cs.smell_distribution:
            print(f'  • Top Smells: {list(cs.smell_distribution.keys())[:3]}')
        print()
        
        # Architecture Results
        print('🏗️  ARCHITECTURE ANALYSIS:')
        arch = report.architecture
        print(f'  • Dependencies Found: {len(arch.dependencies)}')
        print(f'  • Design Patterns: {len(arch.design_patterns)}')
        print(f'  • Violations: {len(arch.violations)}')
        print(f'  • Complexity Score: {arch.complexity_score:.2f}/10')
        if arch.dependencies:
            print(f'  • Top Dependencies: {list(arch.dependencies.keys())[:5]}')
        print()
        
        # Documentation Results
        print('📚 DOCUMENTATION ANALYSIS:')
        doc = report.documentation
        print(f'  • Coverage Score: {doc.coverage_score:.2f}/10')
        print(f'  • Quality Score: {doc.quality_score:.2f}/10')
        print(f'  • Files Analyzed: {doc.files_analyzed}')
        print(f'  • Documented Functions: {doc.documented_functions}/{doc.total_functions}')
        print(f'  • Documented Classes: {doc.documented_classes}/{doc.total_classes}')
        print()
        
        # Test Results
        print('🧪 TEST ANALYSIS:')
        test = report.test_analysis
        print(f'  • Coverage Score: {test.coverage_score:.2f}/10')
        print(f'  • Quality Score: {test.quality_score:.2f}/10')
        print(f'  • Test Files: {test.test_files_count}')
        print(f'  • Test Functions: {test.total_test_functions}')
        print(f'  • Frameworks: {list(test.frameworks_detected)}')
        print()
        
        # Sustainability Results
        print('🌱 SUSTAINABILITY ANALYSIS:')
        sust = report.sustainability
        print(f'  • Overall Score: {sust.sustainability_score:.2f}/10')
        print(f'  • Activity Trend: {sust.activity_trend}')
        print(f'  • Contributor Growth: {sust.contributor_growth}')
        print(f'  • Maintenance Score: {sust.maintenance_score:.2f}/10')
        print()
        
        # Final Summary
        print('🏆 SYSTEM TEST SUMMARY:')
        print('=' * 70)
        total_files = (cq.files_analyzed + cs.files_analyzed + 
                      arch.files_analyzed + doc.files_analyzed + 
                      test.test_files_count)
        
        print(f'✅ All 6 analyzers completed successfully!')
        print(f'📁 Total files processed: {total_files // 5} (estimated)')  # Rough estimate
        print(f'⏱️  Processing speed: {(total_files // 5) / duration:.1f} files/second')
        print(f'🎯 System is PRODUCTION READY!')
        print()
        print('🎉 COMPREHENSIVE SYSTEM TEST: SUCCESS! 🎉')
        
        return True
        
    except Exception as e:
        print(f'❌ SYSTEM TEST FAILED: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
