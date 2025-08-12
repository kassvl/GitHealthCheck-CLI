#!/usr/bin/env python3
"""
Demo script for Repo Health Analyzer.

Creates a sample repository and runs analysis to demonstrate functionality.
"""

import os
import tempfile
import subprocess
from pathlib import Path


def create_sample_repo():
    """Create a sample repository for demonstration."""
    temp_dir = Path(tempfile.mkdtemp(prefix="rha_demo_"))
    
    print(f"Creating sample repository in: {temp_dir}")
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=temp_dir, check=True)
    subprocess.run(["git", "config", "user.email", "demo@example.com"], cwd=temp_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Demo User"], cwd=temp_dir, check=True)
    
    # Create sample Python project
    src_dir = temp_dir / "src"
    src_dir.mkdir()
    
    # Main module with various code patterns
    main_py = src_dir / "main.py"
    main_py.write_text('''
"""Main module for demo project."""

import os
import sys
from typing import List, Optional


def calculate_factorial(n: int) -> int:
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * calculate_factorial(n - 1)


def process_data(data: List[int], threshold: int = 100) -> List[int]:
    """Process data with threshold filtering."""
    result = []
    for item in data:
        if item > threshold:
            result.append(item * 2)
        else:
            result.append(item)
    return result


# This is a long function that should trigger code smell detection
def very_long_function_with_many_responsibilities():
    """This function does too many things and is too long."""
    # Data processing
    data = [1, 2, 3, 4, 5]
    processed = []
    
    for item in data:
        if item % 2 == 0:
            processed.append(item * 2)
        else:
            processed.append(item * 3)
    
    # File operations
    filename = "output.txt"
    with open(filename, "w") as f:
        for item in processed:
            f.write(f"{item}\\n")
    
    # Network operations (simulated)
    import time
    time.sleep(0.1)
    
    # Data validation
    validated = []
    for item in processed:
        if item > 0 and item < 1000:
            validated.append(item)
    
    # Logging
    print(f"Processed {len(validated)} items")
    
    # More processing
    final_result = []
    for item in validated:
        if item > 10:
            final_result.append(item)
    
    return final_result


class DataProcessor:
    """Example class for data processing."""
    
    def __init__(self, config: dict):
        self.config = config
        self.processed_count = 0
    
    def process_item(self, item: Any) -> Any:
        """Process a single item."""
        self.processed_count += 1
        return item * 2
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {"processed": self.processed_count}


# Magic numbers example
def calculate_score(base_score):
    """Calculate final score with magic numbers."""
    bonus = base_score * 0.15  # Magic number
    if bonus > 50:  # Another magic number
        bonus = 50
    return base_score + bonus
''')
    
    # Test file
    test_py = src_dir / "test_main.py"
    test_py.write_text('''
"""Test module for main.py."""

import unittest
from main import calculate_factorial, process_data, DataProcessor


class TestMain(unittest.TestCase):
    """Test cases for main module."""
    
    def test_factorial(self):
        """Test factorial calculation."""
        self.assertEqual(calculate_factorial(0), 1)
        self.assertEqual(calculate_factorial(1), 1)
        self.assertEqual(calculate_factorial(5), 120)
    
    def test_factorial_negative(self):
        """Test factorial with negative input."""
        with self.assertRaises(ValueError):
            calculate_factorial(-1)
    
    def test_process_data(self):
        """Test data processing."""
        data = [50, 150, 75, 200]
        result = process_data(data, 100)
        expected = [50, 300, 75, 400]
        self.assertEqual(result, expected)
    
    def test_data_processor(self):
        """Test DataProcessor class."""
        processor = DataProcessor({"mode": "test"})
        result = processor.process_item(5)
        self.assertEqual(result, 10)
        
        stats = processor.get_stats()
        self.assertEqual(stats["processed"], 1)


if __name__ == '__main__':
    unittest.main()
''')
    
    # README
    readme = temp_dir / "README.md"
    readme.write_text('''
# Demo Project

This is a demonstration project for testing the Repo Health Analyzer.

## Features

- Factorial calculation
- Data processing
- Example class structure

## Installation

```bash
pip install -e .
```

## Usage

```python
from src.main import calculate_factorial
result = calculate_factorial(5)
print(result)  # 120
```

## Testing

```bash
python -m unittest discover -s src -p "test_*.py"
```

## Contributing

Please follow the coding standards and add tests for new features.
''')
    
    # Requirements file
    requirements = temp_dir / "requirements.txt"
    requirements.write_text('''
# Demo project dependencies
typing-extensions>=4.0.0
''')
    
    # Add files to git
    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)
    
    # Add more commits to simulate development
    main_py.write_text(main_py.read_text() + '''

def new_feature():
    """A new feature added later."""
    return "new feature"
''')
    
    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Add new feature"], cwd=temp_dir, check=True)
    
    return temp_dir


def run_demo():
    """Run the complete demo."""
    print("🎭 Repo Health Analyzer Demo")
    print("=" * 40)
    
    # Create sample repository
    demo_repo = create_sample_repo()
    
    try:
        print(f"\\n📁 Sample repository created at: {demo_repo}")
        
        # Run analysis
        print("\\n🔍 Running repository analysis...")
        
        # Change to demo repository
        original_cwd = os.getcwd()
        os.chdir(demo_repo)
        
        # Run RHA analysis
        result = subprocess.run(
            ["rha", "analyze", "--verbose", "--visualize"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Analysis completed successfully!")
            print("\\nOutput:")
            print(result.stdout)
            
            # Show generated files
            print("\\n📊 Generated files:")
            for file in demo_repo.glob("*.json"):
                print(f"  - {file.name}")
            for file in demo_repo.glob("*.svg"):
                print(f"  - {file.name}")
        else:
            print("❌ Analysis failed:")
            print(result.stderr)
        
        # Return to original directory
        os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        # Clean up
        import shutil
        try:
            shutil.rmtree(demo_repo)
            print(f"\\n🧹 Cleaned up demo repository: {demo_repo}")
        except Exception:
            print(f"\\n⚠️ Could not clean up demo repository: {demo_repo}")


if __name__ == "__main__":
    run_demo()
