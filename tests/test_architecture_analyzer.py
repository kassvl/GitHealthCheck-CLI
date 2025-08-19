"""Tests for Architecture Analyzer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from repo_health_analyzer.core.analyzers.architecture_analyzer import ArchitectureAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestArchitectureAnalyzer:
    """Test cases for Architecture Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return ArchitectureAnalyzer(config)
    
    @pytest.fixture
    def sample_python_mvc_code(self):
        """Sample Python MVC code for testing."""
        return '''
from abc import ABC, abstractmethod
import sqlite3

class UserModel:
    """User model following MVC pattern."""
    
    def __init__(self, database):
        self.db = database
    
    def get_user(self, user_id):
        return self.db.execute("SELECT * FROM users WHERE id = ?", (user_id,))

class UserController:
    """User controller following MVC pattern."""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
    
    def show_user(self, user_id):
        if isinstance(user_id, int):  # OCP violation
            user = self.model.get_user(user_id)
            return self.view.render_user(user)
        raise NotImplementedError("Invalid user ID")  # LSP violation

class UserView:
    """User view following MVC pattern."""
    
    def render_user(self, user):
        return f"User: {user['name']}"

class AbstractFactory(ABC):
    """Abstract factory pattern."""
    
    @abstractmethod
    def create_user(self):
        pass

class DatabaseFactory(AbstractFactory):
    """Concrete factory implementation."""
    
    def create_user(self):
        return UserModel(sqlite3.connect("users.db"))

# Singleton pattern
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
'''
    
    @pytest.fixture
    def sample_dependency_code(self):
        """Sample code with dependencies."""
        return '''
import os
import sys
from pathlib import Path
from typing import List, Dict
from .models import User, Product
from ..utils import helper_function
from external_lib import external_function

class ServiceClass:
    def method_with_chain(self):
        return self.service.user.profile.name  # Law of Demeter violation
'''
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.dependency_patterns is not None
        assert analyzer.architecture_patterns is not None
        assert analyzer.design_patterns is not None
        assert 'python' in analyzer.dependency_patterns
        assert 'mvc_controller' in analyzer.architecture_patterns
        assert 'solid_srp' in analyzer.design_patterns
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language('.py') == 'python'
        assert analyzer._detect_language('.js') == 'javascript'
        assert analyzer._detect_language('.java') == 'java'
        assert analyzer._detect_language('.unknown') == 'generic'
    
    def test_extract_dependencies_python(self, analyzer, sample_dependency_code):
        """Test dependency extraction for Python."""
        patterns = analyzer.dependency_patterns['python']
        dependencies = analyzer._extract_dependencies(sample_dependency_code, patterns)
        
        assert len(dependencies) > 0
        assert 'pathlib' in dependencies or 'typing' in dependencies
        # Built-in modules should be filtered out
        assert 'os' not in dependencies
        assert 'sys' not in dependencies
    
    def test_is_builtin_module(self, analyzer):
        """Test built-in module detection."""
        assert analyzer._is_builtin_module('os') == True
        assert analyzer._is_builtin_module('sys') == True
        assert analyzer._is_builtin_module('json') == True
        assert analyzer._is_builtin_module('custom_module') == False
        assert analyzer._is_builtin_module('java.util') == True
    
    def test_extract_inheritance_python(self, analyzer, sample_python_mvc_code):
        """Test inheritance extraction for Python."""
        patterns = analyzer.dependency_patterns['python']
        inheritance = analyzer._extract_inheritance(sample_python_mvc_code, patterns, 'python')
        
        # Should detect AbstractFactory inheriting from ABC
        assert len(inheritance) > 0
    
    def test_detect_design_patterns(self, analyzer, sample_python_mvc_code):
        """Test design pattern detection."""
        patterns_found = analyzer._detect_design_patterns(sample_python_mvc_code, Path('user_service.py'))
        
        assert 'singleton_pattern' in patterns_found  # ConfigManager singleton
        assert 'factory_pattern' in patterns_found or 'mvc_model' in patterns_found
    
    def test_detect_architecture_violations(self, analyzer, sample_python_mvc_code):
        """Test architecture violation detection."""
        violations = analyzer._detect_architecture_violations(sample_python_mvc_code, Path('test.py'))
        
        assert len(violations) > 0
        violation_types = [v['type'] for v in violations]
        assert 'solid_ocp' in violation_types  # isinstance check
        assert 'solid_lsp' in violation_types  # NotImplementedError
    
    def test_analyze_complexity_indicators(self, analyzer, sample_python_mvc_code):
        """Test complexity indicator analysis."""
        patterns = analyzer.dependency_patterns['python']
        indicators = analyzer._analyze_complexity_indicators(sample_python_mvc_code, patterns)
        
        assert 'class_count' in indicators
        assert 'function_count' in indicators
        assert 'method_calls' in indicators
        assert indicators['class_count'] > 0
        assert indicators['function_count'] > 0
    
    def test_get_module_name(self, analyzer):
        """Test module name extraction."""
        file_path = Path('/path/to/user_service.py')
        module_name = analyzer._get_module_name(file_path)
        assert module_name == 'user_service'
    
    def test_get_package_name(self, analyzer):
        """Test package name extraction."""
        file_path = Path('/path/to/services/user_service.py')
        package_name = analyzer._get_package_name(file_path)
        assert package_name == 'services'
    
    def test_get_violation_description(self, analyzer):
        """Test violation description retrieval."""
        desc = analyzer._get_violation_description('solid_srp')
        assert 'Single Responsibility Principle' in desc
        
        desc = analyzer._get_violation_description('unknown_violation')
        assert 'Architecture violation: unknown_violation' in desc
    
    def test_detect_circular_dependencies(self, analyzer):
        """Test circular dependency detection."""
        # Create a simple circular dependency graph
        dependency_graph = {
            'module_a': {'module_b'},
            'module_b': {'module_c'},
            'module_c': {'module_a'}  # Creates a cycle
        }
        
        cycles = analyzer._detect_circular_dependencies(dependency_graph)
        assert len(cycles) > 0
        
        # Test graph without cycles
        acyclic_graph = {
            'module_a': {'module_b'},
            'module_b': {'module_c'},
            'module_c': set()
        }
        
        cycles = analyzer._detect_circular_dependencies(acyclic_graph)
        assert len(cycles) == 0
    
    def test_calculate_inheritance_depth(self, analyzer):
        """Test inheritance depth calculation."""
        hierarchy = {
            'Child': ['Parent'],
            'Parent': ['GrandParent'],
            'GrandParent': []
        }
        
        depth = analyzer._calculate_inheritance_depth('Child', hierarchy, set())
        assert depth == 3  # Child -> Parent -> GrandParent
        
        depth = analyzer._calculate_inheritance_depth('Parent', hierarchy, set())
        assert depth == 2  # Parent -> GrandParent
        
        depth = analyzer._calculate_inheritance_depth('GrandParent', hierarchy, set())
        assert depth == 1  # No parents
    
    def test_calculate_inheritance_depth_circular(self, analyzer):
        """Test inheritance depth with circular reference."""
        circular_hierarchy = {
            'A': ['B'],
            'B': ['A']  # Circular reference
        }
        
        depth = analyzer._calculate_inheritance_depth('A', circular_hierarchy, set())
        assert depth == 0  # Should handle circular reference
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_architecture(self, analyzer, sample_python_mvc_code):
        """Test file architecture analysis."""
        with patch('builtins.open', mock_open(read_data=sample_python_mvc_code)):
            test_file = Path('test.py')
            result = analyzer._analyze_file_architecture(test_file)
            
            assert result is not None
            assert 'language' in result
            assert 'dependencies' in result
            assert 'inheritance' in result
            assert 'patterns' in result
            assert 'violations' in result
            assert result['language'] == 'python'
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_file_architecture_error(self, mock_open, analyzer):
        """Test file architecture analysis with IO error."""
        test_file = Path('nonexistent.py')
        result = analyzer._analyze_file_architecture(test_file)
        assert result == {}
    
    def test_calculate_architecture_metrics(self, analyzer):
        """Test architecture metrics calculation."""
        dependency_graph = {
            'module_a': {'module_b', 'module_c'},
            'module_b': {'module_c'},
            'module_c': set()
        }
        
        module_dependencies = dependency_graph
        class_hierarchy = {'Child': ['Parent'], 'Parent': []}
        package_structure = {'package1': ['module_a', 'module_b'], 'package2': ['module_c']}
        design_patterns = {'singleton_pattern': 1, 'factory_pattern': 2}
        violations = [
            {'type': 'solid_srp', 'file': 'test.py'},
            {'type': 'solid_ocp', 'file': 'test.py'}
        ]
        language_stats = {'python': 3}
        total_files = 3
        
        metrics = analyzer._calculate_architecture_metrics(
            dependency_graph, module_dependencies, class_hierarchy,
            package_structure, design_patterns, violations,
            language_stats, total_files
        )
        
        assert 'overall_score' in metrics
        assert 'dependency_count' in metrics
        assert 'circular_dependencies' in metrics
        assert 'coupling_score' in metrics
        assert 'cohesion_score' in metrics
        assert 'srp_violations' in metrics
        assert 'module_count' in metrics
        assert 'depth_of_inheritance' in metrics
        
        assert 0 <= metrics['overall_score'] <= 10
        assert metrics['dependency_count'] == 3  # Total dependencies
        assert metrics['circular_dependencies'] == 0  # No cycles in test graph
        assert metrics['srp_violations'] == 1  # One SRP violation
        assert metrics['module_count'] == 3  # Three modules
    
    def test_generate_architecture_insights(self, analyzer):
        """Test architecture insights generation."""
        dependency_graph = {'module_a': {'dep1', 'dep2', 'dep3'}, 'module_b': {'dep1'}}
        design_patterns = {'singleton_pattern': 1, 'factory_pattern': 2}
        violations = [
            {'type': 'solid_srp', 'file': 'test.py'},
            {'type': 'solid_ocp', 'file': 'test.py'}
        ]
        
        insights = analyzer._generate_architecture_insights(dependency_graph, design_patterns, violations)
        
        assert 'recommendations' in insights
        assert 'design_patterns_used' in insights
        assert 'top_violations' in insights
        assert 'dependency_hotspots' in insights
        
        assert 'singleton_pattern' in insights['design_patterns_used']
        assert 'factory_pattern' in insights['design_patterns_used']
        assert len(insights['dependency_hotspots']) > 0
    
    @patch('builtins.open', mock_open())
    def test_analyze_integration(self, analyzer, sample_python_mvc_code):
        """Test full analysis integration."""
        with patch('builtins.open', mock_open(read_data=sample_python_mvc_code)):
            test_files = [Path('test1.py'), Path('test2.py')]
            result = analyzer.analyze(test_files)
            
            assert result is not None
            assert hasattr(result, 'score')
            assert hasattr(result, 'dependency_count')
            assert hasattr(result, 'circular_dependencies')
            assert hasattr(result, 'coupling_score')
            assert hasattr(result, 'cohesion_score')
            assert 0 <= result.score <= 10
    
    def test_empty_file_list(self, analyzer):
        """Test analysis with empty file list."""
        result = analyzer.analyze([])
        assert result is not None
        assert result.score >= 0
    
    def test_javascript_dependency_extraction(self, analyzer):
        """Test JavaScript dependency extraction."""
        js_code = '''
import React from 'react';
import { Component } from 'react';
const express = require('express');
const fs = require('fs');
export default class MyComponent extends Component {}
'''
        patterns = analyzer.dependency_patterns['javascript']
        dependencies = analyzer._extract_dependencies(js_code, patterns)
        
        assert 'react' in dependencies
        assert 'express' in dependencies
        # Built-ins should be filtered
        assert 'fs' not in dependencies
    
    def test_java_dependency_extraction(self, analyzer):
        """Test Java dependency extraction."""
        java_code = '''
import java.util.List;
import java.io.IOException;
import com.example.UserService;
import org.springframework.Service;

@Service
public class UserController {
    private UserService userService;
}
'''
        patterns = analyzer.dependency_patterns['java']
        dependencies = analyzer._extract_dependencies(java_code, patterns)
        
        # Should contain custom imports but not built-ins
        assert 'com.example.UserService' in dependencies or 'org.springframework.Service' in dependencies
        assert 'java.util' not in dependencies  # Built-in should be filtered


if __name__ == '__main__':
    pytest.main([__file__])
