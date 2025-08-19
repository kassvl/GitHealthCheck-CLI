"""
Simple command line interface for the Repository Health Analyzer.
"""

import argparse
import sys
import json
from pathlib import Path

from ..core.analyzer import RepositoryAnalyzer
from ..models.simple_report import AnalysisConfig


def main():
    parser = argparse.ArgumentParser(
        description="Repository Health Analyzer - Comprehensive code quality analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/repo                    # Basic analysis
  %(prog)s /path/to/repo --verbose          # Verbose output
  %(prog)s /path/to/repo -o report.json     # Save to file
  %(prog)s /path/to/repo --max-files 500    # Limit analysis
  %(prog)s /path/to/repo --max-files 1000   # Limit file processing
        """
    )
    
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    # Visualization disabled - CLI-only mode
    # GUI disabled - CLI-only mode
    parser.add_argument("--max-files", type=int, default=1000, help="Maximum files to analyze")
    parser.add_argument("--include", nargs="+", default=['*.py', '*.js', '*.java', '*.ts', '*.md'], 
                       help="File patterns to include")
    parser.add_argument("--exclude", nargs="+", 
                       default=['*/venv/*', '*/node_modules/*', '*/build/*', '*/.git/*'], 
                       help="File patterns to exclude")
    
    args = parser.parse_args()
    
    # Pure CLI mode - no GUI
    if not args.repo_path:
        parser.print_help()
        print("\n❌ Error: Repository path is required")
        sys.exit(1)
    
    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"❌ Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    if not (repo_path / ".git").exists():
        print(f"❌ Error: Not a Git repository: {repo_path}")
        print("💡 Run 'git init' in the directory or choose a Git repository")
        sys.exit(1)
    
    # Configure analysis
    config = AnalysisConfig()
    config.max_files = args.max_files
    config.include_patterns = args.include
    config.exclude_patterns = args.exclude
    
    analyzer = RepositoryAnalyzer(repo_path, config, verbose=args.verbose)
    
    print(f"🔍 Analyzing repository: {repo_path}")
    print(f"📊 Max files: {config.max_files}")
    print(f"🎯 Include: {', '.join(config.include_patterns)}")
    print("=" * 60)
    
    try:
        report = analyzer.analyze()
        
        # Calculate overall score
        # Use the calculated overall score from the report
        overall_score = report.metrics.overall_score
        
        # Display results
        print("✅ Analysis completed successfully!")
        print("=" * 60)
        print(f"🏆 Overall Health Score: {overall_score:.1f}/10")
        print()
        print("📊 Category Scores:")
        print(f"  🎯 Code Quality:     {report.metrics.code_quality.overall_score:.1f}/10")
        print(f"  🏗️  Architecture:     {report.metrics.architecture.score:.1f}/10") 
        print(f"  👃 Code Smells:      {(10 - min(report.metrics.code_smells.severity_score, 10)):.1f}/10")
        print(f"  🧪 Test Coverage:    {report.metrics.tests.coverage_score:.1f}/10")
        print(f"  📚 Documentation:    {report.metrics.documentation.score:.1f}/10")
        print(f"  ♻️  Sustainability:   {report.metrics.sustainability.score:.1f}/10")
        print()
        print("📈 Key Metrics:")
        print(f"  📁 Repository:       {report.repository.name}")
        print(f"  🗂️  Languages:        {list(report.repository.languages.keys())}")
        contributors_count = report.repository.contributors if isinstance(report.repository.contributors, int) else len(report.repository.contributors)
        print(f"  👥 Contributors:     {contributors_count}")
        print(f"  🔗 Dependencies:     {report.metrics.architecture.dependency_count}")
        print(f"  🧪 Test Files:       {report.metrics.tests.test_files_count}")
        print(f"  👃 Total Smells:     {report.metrics.code_smells.total_count}")
        
        # Visualization disabled - CLI-only mode
        print("📊 Pure CLI mode - no visualizations generated")
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            report_data = {
                'repository': {
                    'name': report.repository.name,
                    'path': str(report.repository.path),
                    'total_files': report.repository.total_files,
                    'total_lines': report.repository.total_lines,
                    'languages': report.repository.languages or {},
                    'contributors': contributors_count,
                    'commit_count': report.repository.commit_count,
                    'analyzed_at': report.repository.analyzed_at.isoformat() if report.repository.analyzed_at else None
                },
                'overall_score': report.metrics.overall_score,
                'code_quality': report.metrics.code_quality.__dict__,
                'architecture': report.metrics.architecture.__dict__,
                'code_smells': report.metrics.code_smells.__dict__,
                'test_analysis': report.metrics.tests.__dict__,
                'documentation': report.metrics.documentation.__dict__,
                'sustainability': report.metrics.sustainability.__dict__
            }
            
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"💾 Report saved to: {output_path}")
        
        # Status indication
        if overall_score >= 8:
            print("\n🎉 Excellent! Your repository is in great health!")
        elif overall_score >= 6:
            print("\n👍 Good! Your repository is well maintained with room for improvement.")
        elif overall_score >= 4:
            print("\n⚠️  Fair. Your repository needs attention in several areas.")
        else:
            print("\n🚨 Critical! Your repository requires immediate attention.")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

