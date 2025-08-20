"""
Main CLI interface for Repo Health Analyzer.

Provides commands for analyzing git repositories and generating health reports.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from ..core.analyzer import RepositoryAnalyzer
from ..models.simple_report import HealthReport

# Version information
__version__ = "1.0.0"

def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"Repo Health Analyzer (rha) version {__version__}")
        raise typer.Exit()

app = typer.Typer(
    name="rha",
    help="Repo Health Analyzer - Offline git repository health analysis tool",
    add_completion=False,
)
console = Console()


@app.command()
def analyze(
    repo_path: Optional[str] = typer.Argument(
        None, help="Path to git repository (defaults to current directory)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path for health report JSON"
    ),
    # Visualization disabled - CLI-only mode
    verbose: bool = typer.Option(
        False, "--verbose", help="Enable verbose output"
    ),
    format_type: str = typer.Option(
        "json", "--format", help="Output format: json, yaml, or summary"
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True,
        help="Show version and exit"
    ),
) -> None:
    """
    Analyze a git repository and generate a comprehensive health report.
    
    This command performs offline analysis of code quality, architecture,
    code smells, test coverage, documentation, and sustainability prediction.
    """
    # Determine repository path
    if repo_path is None:
        repo_path_str = os.getcwd()
    else:
        repo_path_str = repo_path
    
    repo_path_obj = Path(repo_path_str).resolve()
    
    if not repo_path_obj.exists():
        console.print(f"[red]Error: Repository path does not exist: {repo_path_obj}[/red]")
        sys.exit(1)
    
    if not (repo_path_obj / ".git").exists():
        console.print(f"[red]Error: Not a git repository: {repo_path_obj}[/red]")
        sys.exit(1)
    
    console.print(f"[green]Analyzing repository:[/green] {repo_path}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize analyzer
            task = progress.add_task("Initializing analyzer...", total=None)
            analyzer = RepositoryAnalyzer(repo_path_obj, verbose=verbose)
            
            # Run analysis
            progress.update(task, description="Running comprehensive analysis...")
            health_report = analyzer.analyze()
            
            progress.update(task, description="Generating report...")
            
            # Visualization disabled - CLI-only mode
            console.print("[blue]📊 Pure CLI mode - no visualizations generated[/blue]")
            
            progress.update(task, description="Finalizing report...")
        
        # Display summary
        _display_summary(health_report)
        
        # Save report
        output_path = output or "health_report.json"
        if format_type == "json":
            with open(output_path, "w") as f:
                json.dump(health_report.__dict__, f, indent=2, default=str)
        elif format_type == "yaml":
            import yaml
            output_path = output or "health_report.yaml"
            with open(output_path, "w") as f:
                yaml.dump(health_report.__dict__, f, default_flow_style=False)
        elif format_type == "summary":
            output_path = output or "health_summary.txt"
            with open(output_path, "w") as f:
                f.write(_generate_text_summary(health_report))
        
        console.print(f"[green]✓[/green] Health report saved to: {output_path}")
        
        # Visualization disabled - CLI-only mode
        console.print("[blue]📊[/blue] Pure CLI mode - no visualization files generated")
        
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from .. import __version__
    console.print(f"Repo Health Analyzer v{__version__}")


@app.command()
def validate(
    repo_path: Optional[str] = typer.Argument(
        None, help="Path to git repository (defaults to current directory)"
    ),
) -> None:
    """
    Validate that a repository can be analyzed.
    
    Performs quick checks to ensure the repository is suitable for analysis.
    """
    if repo_path is None:
        repo_path_str = os.getcwd()
    else:
        repo_path_str = repo_path
    
    repo_path_obj = Path(repo_path_str).resolve()
    
    console.print(f"[blue]Validating repository:[/blue] {repo_path_obj}")
    
    checks = [
        ("Repository exists", repo_path_obj.exists()),
        ("Is git repository", (repo_path_obj / ".git").exists()),
        ("Has source files", _has_source_files(repo_path_obj)),
        ("Readable permissions", os.access(repo_path_obj, os.R_OK)),
    ]
    
    table = Table(title="Repository Validation")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "green" if passed else "red"
        table.add_row(check_name, f"[{color}]{status}[/{color}]")
        if not passed:
            all_passed = False
    
    console.print(table)
    
    if all_passed:
        console.print("[green]✓ Repository is ready for analysis[/green]")
    else:
        console.print("[red]✗ Repository validation failed[/red]")
        sys.exit(1)


def _has_source_files(repo_path: Path) -> bool:
    """Check if repository contains source files."""
    source_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if Path(file).suffix.lower() in source_extensions:
                return True
    return False


def _display_summary(report: HealthReport) -> None:
    """Display a rich summary of the health report."""
    
    # Overall health panel
    overall_score = report.metrics.overall_score
    score_color = "green" if overall_score >= 8 else "yellow" if overall_score >= 6 else "red"
    
    console.print(Panel(
        f"[bold {score_color}]Overall Health Score: {overall_score:.1f}/10[/bold {score_color}]",
        title="Repository Health Summary",
        expand=False
    ))
    
    # Metrics table
    table = Table(title="Detailed Metrics")
    table.add_column("Category", style="cyan")
    table.add_column("Score", style="bold")
    table.add_column("Status", style="green")
    
    metrics = [
        ("Code Quality", report.metrics.code_quality.overall_score),
        ("Architecture", report.metrics.architecture.score),
        ("Code Smells", 10 - min(report.metrics.code_smells.severity_score, 10)),
        ("Test Coverage", report.metrics.tests.coverage_score),
        ("Documentation", report.metrics.documentation.score),
        ("Sustainability", report.metrics.sustainability.score),
    ]
    
    for category, score in metrics:
        score_str = f"{score:.1f}/10"
        if score >= 8:
            status = "🟢 Excellent"
        elif score >= 6:
            status = "🟡 Good"
        elif score >= 4:
            status = "🟠 Needs Work"
        else:
            status = "🔴 Critical"
        
        table.add_row(category, score_str, status)
    
    console.print(table)
    
    # Top recommendations
    if report.recommendations:
        console.print("\n[bold cyan]Top Recommendations:[/bold cyan]")
        for i, rec in enumerate(report.recommendations[:5], 1):
            console.print(f"{i}. {rec.description} (Priority: {rec.priority})")


def _generate_text_summary(report: HealthReport) -> str:
    """Generate a text-based summary of the health report."""
    lines = [
        f"Repository Health Report - {report.repository.name}",
        "=" * 50,
        f"Analyzed at: {report.repository.analyzed_at}",
        f"Repository path: {report.repository.path}",
        "",
        f"Overall Health Score: {report.metrics.overall_score:.1f}/10",
        "",
        "Detailed Metrics:",
        f"  Code Quality: {report.metrics.code_quality.overall_score:.1f}/10",
        f"  Architecture: {report.metrics.architecture.score:.1f}/10",
        f"  Code Smells: {10 - min(report.metrics.code_smells.severity_score, 10):.1f}/10",
        f"  Test Coverage: {report.metrics.tests.coverage_score:.1f}/10",
        f"  Documentation: {report.metrics.documentation.score:.1f}/10",
        f"  Sustainability: {report.metrics.sustainability.score:.1f}/10",
        "",
    ]
    
    if report.recommendations:
        lines.extend([
            "Top Recommendations:",
            "-" * 20,
        ])
        for i, rec in enumerate(report.recommendations[:10], 1):
            lines.append(f"{i}. {rec.description} (Priority: {rec.priority})")
    
    return "\n".join(lines)


if __name__ == "__main__":
    app()
