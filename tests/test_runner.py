#!/usr/bin/env python3
"""Test runner script for Repository Health Analyzer."""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all tests with coverage reporting."""
    print("🧪 Running Repository Health Analyzer Tests...")
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    
    # Test commands
    commands = [
        # Run tests with coverage
        [
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', 
            '--cov=repo_health_analyzer',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--tb=short'
        ],
        
        # Run specific test categories
        [
            sys.executable, '-m', 'pytest',
            'tests/test_code_quality_analyzer.py',
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_architecture_analyzer.py', 
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_code_smell_analyzer.py',
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_documentation_analyzer.py',
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_sustainability_analyzer.py',
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_test_analyzer.py',
            '-v', '--tb=short'
        ],
        
        [
            sys.executable, '-m', 'pytest',
            'tests/test_integration.py',
            '-v', '--tb=short'
        ]
    ]
    
    print(f"📁 Working directory: {project_root}")
    
    # Run main test suite
    print("\n🚀 Running main test suite with coverage...")
    result = subprocess.run(commands[0], cwd=project_root, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        print(f"Exit code: {result.returncode}")
    
    # Run individual test modules
    print("\n📊 Running individual test modules...")
    
    for i, cmd in enumerate(commands[1:], 1):
        test_name = cmd[3].split('/')[-1].replace('.py', '').replace('test_', '')
        print(f"\n{i}. Testing {test_name}...")
        
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {test_name} tests passed")
        else:
            print(f"   ❌ {test_name} tests failed")
            if result.stdout:
                print(f"   Output: {result.stdout[-200:]}")  # Last 200 chars
    
    print("\n📈 Test Summary:")
    print("   - Code Quality Analyzer Tests")
    print("   - Architecture Analyzer Tests") 
    print("   - Code Smell Analyzer Tests")
    print("   - Documentation Analyzer Tests")
    print("   - Sustainability Analyzer Tests")
    print("   - Test Analyzer Tests")
    print("   - Integration Tests")
    print("   - Main Analyzer Tests")
    print("   - Orchestrator Tests")
    
    print(f"\n📊 Coverage report generated in: {project_root}/htmlcov/index.html")
    
    return result.returncode


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
