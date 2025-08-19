"""Tests for Code Smell Analyzer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from repo_health_analyzer.core.analyzers.code_smell_analyzer import CodeSmellAnalyzer
from repo_health_analyzer.models.simple_report import AnalysisConfig


class TestCodeSmellAnalyzer:
    """Test cases for Code Smell Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        config = AnalysisConfig()
        return CodeSmellAnalyzer(config)
    
    @pytest.fixture
    def long_method_code(self):
        """Sample code with long method smell."""
        return '''
def very_long_method():
    """This method is too long and does too many things."""
    # Line 1
    x = 1
    # Line 2
    y = 2
    # Line 3
    z = 3
    # Line 4
    a = 4
    # Line 5
    b = 5
    # Continue for 50+ lines...
    ''' + '\n'.join([f'    # Line {i}' for i in range(6, 55)]) + '''
    return x + y + z + a + b
'''
    
    @pytest.fixture
    def duplicate_code(self):
        """Sample code with duplication smell."""
        return '''
def calculate_area_rectangle(width, height):
    if width <= 0 or height <= 0:
        raise ValueError("Invalid dimensions")
    return width * height

def calculate_area_triangle(base, height):
    if base <= 0 or height <= 0:
        raise ValueError("Invalid dimensions")
    return 0.5 * base * height

def calculate_area_circle(radius):
    if radius <= 0:
        raise ValueError("Invalid dimensions")
    return 3.14159 * radius * radius
'''
    
    @pytest.fixture
    def god_class_code(self):
        """Sample code with god class smell."""
        return '''
class UserManager:
    """This class does too many things - God Class smell."""
    
    def __init__(self):
        self.users = []
        self.database = None
        self.logger = None
        self.email_service = None
        self.notification_service = None
    
    def create_user(self, name, email): pass
    def update_user(self, user_id, data): pass
    def delete_user(self, user_id): pass
    def get_user(self, user_id): pass
    def list_users(self): pass
    def validate_email(self, email): pass
    def hash_password(self, password): pass
    def send_welcome_email(self, user): pass
    def send_notification(self, user, message): pass
    def log_activity(self, action, user): pass
    def backup_database(self): pass
    def restore_database(self): pass
    def generate_report(self): pass
    def export_users(self, format): pass
    def import_users(self, file): pass
    def calculate_statistics(self): pass
    def cleanup_old_data(self): pass
    def migrate_data(self): pass
    def validate_permissions(self, user, action): pass
    def audit_changes(self, changes): pass
    def compress_data(self): pass
    def encrypt_sensitive_data(self): pass
    def decrypt_sensitive_data(self): pass
    def handle_errors(self, error): pass
    def format_output(self, data): pass
'''
    
    @pytest.fixture
    def magic_numbers_code(self):
        """Sample code with magic numbers."""
        return '''
def calculate_discount(price, customer_type):
    if customer_type == 1:  # Magic number
        return price * 0.95  # 5% discount
    elif customer_type == 2:  # Magic number
        return price * 0.90  # 10% discount
    elif customer_type == 3:  # Magic number
        return price * 0.85  # 15% discount
    else:
        return price

def process_payment(amount):
    tax_rate = 0.08  # Magic number
    processing_fee = 2.50  # Magic number
    maximum_amount = 10000  # Magic number
    
    if amount > maximum_amount:
        return False
    
    total = amount + (amount * tax_rate) + processing_fee
    return total
'''
    
    @pytest.fixture
    def feature_envy_code(self):
        """Sample code with feature envy smell."""
        return '''
class Order:
    def __init__(self, customer):
        self.customer = customer
        self.items = []
    
    def calculate_total_discount(self):
        # This method envies Customer class features
        discount = 0
        if self.customer.membership.level == "gold":
            discount += self.customer.membership.discount_rate
        if self.customer.profile.age > 65:
            discount += self.customer.profile.senior_discount
        if self.customer.history.purchase_count > 100:
            discount += self.customer.history.loyalty_bonus
        return discount
'''
    
    @pytest.fixture
    def long_parameter_list_code(self):
        """Sample code with long parameter list smell."""
        return '''
def create_user_account(first_name, last_name, email, phone, address_line1, 
                       address_line2, city, state, zip_code, country, 
                       birth_date, gender, occupation, company, department,
                       manager_email, emergency_contact_name, emergency_contact_phone):
    """This method has too many parameters."""
    pass

def update_product(product_id, name, description, price, category, brand,
                  weight, dimensions_length, dimensions_width, dimensions_height,
                  color, material, manufacturer, warranty_period, stock_quantity,
                  min_stock_level, max_stock_level, supplier_id, tags):
    """Another method with too many parameters."""
    pass
'''
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert analyzer.smell_patterns is not None
        assert analyzer.language_patterns is not None
        assert analyzer.severity_weights is not None
        
        # Check smell patterns
        assert 'long_method' in analyzer.smell_patterns
        assert 'duplicate_code' in analyzer.smell_patterns
        assert 'large_class' in analyzer.smell_patterns
        
        # Check severity weights
        assert 'critical' in analyzer.severity_weights
        assert 'high' in analyzer.severity_weights
        assert 'medium' in analyzer.severity_weights
        assert 'low' in analyzer.severity_weights
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language('.py') == 'python'
        assert analyzer._detect_language('.js') == 'javascript'
        assert analyzer._detect_language('.java') == 'java'
        assert analyzer._detect_language('.unknown') == 'generic'
    
    def test_calculate_code_block_size(self, analyzer, long_method_code):
        """Test code block size calculation."""
        size = analyzer._calculate_code_block_size(long_method_code)
        assert size > 50  # Should detect long method
    
    def test_find_duplicate_blocks(self, analyzer, duplicate_code):
        """Test duplicate code block detection."""
        duplicates = analyzer._find_duplicate_blocks(duplicate_code)
        assert len(duplicates) > 0  # Should find duplicated validation logic
        
        for dup in duplicates:
            assert 'line' in dup
            assert 'size' in dup
            assert 'occurrences' in dup
            assert 'context' in dup
            assert dup['occurrences'] > 1
    
    def test_extract_context(self, analyzer):
        """Test context extraction around specific lines."""
        lines = [
            "line 1",
            "line 2", 
            "target line",
            "line 4",
            "line 5"
        ]
        context = analyzer._extract_context(lines, 3, context_size=1)
        assert "line 2" in context
        assert "target line" in context
        assert "line 4" in context
    
    def test_get_smell_suggestion(self, analyzer):
        """Test refactoring suggestion retrieval."""
        suggestion = analyzer._get_smell_suggestion('long_method')
        assert 'Extract Method' in suggestion
        
        suggestion = analyzer._get_smell_suggestion('duplicate_code')
        assert 'Extract' in suggestion or 'shared' in suggestion
        
        suggestion = analyzer._get_smell_suggestion('unknown_smell')
        assert 'refactoring' in suggestion.lower()
    
    def test_calculate_file_smell_score(self, analyzer):
        """Test file smell score calculation."""
        smells = [
            {'severity': 'high', 'type': 'long_method'},
            {'severity': 'medium', 'type': 'duplicate_code'},
            {'severity': 'low', 'type': 'magic_numbers'}
        ]
        
        score = analyzer._calculate_file_smell_score(smells)
        assert score > 0
        
        # Test empty smells
        empty_score = analyzer._calculate_file_smell_score([])
        assert empty_score == 0.0
    
    def test_calculate_severity_score(self, analyzer):
        """Test severity score calculation."""
        from collections import Counter
        
        severity_distribution = Counter({
            'critical': 2,
            'high': 3,
            'medium': 5,
            'low': 10
        })
        
        score = analyzer._calculate_severity_score(severity_distribution)
        assert 0 <= score <= 10
        
        # Test empty distribution
        empty_score = analyzer._calculate_severity_score(Counter())
        assert empty_score == 10.0  # Perfect score for no smells
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_long_method(self, analyzer, long_method_code):
        """Test long method smell detection."""
        with patch('builtins.open', mock_open(read_data=long_method_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'long_method' in smell_types
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_duplicate_code(self, analyzer, duplicate_code):
        """Test duplicate code smell detection."""
        with patch('builtins.open', mock_open(read_data=duplicate_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'duplicate_code' in smell_types
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_god_class(self, analyzer, god_class_code):
        """Test god class smell detection."""
        with patch('builtins.open', mock_open(read_data=god_class_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'large_class' in smell_types
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_magic_numbers(self, analyzer, magic_numbers_code):
        """Test magic numbers smell detection."""
        with patch('builtins.open', mock_open(read_data=magic_numbers_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'magic_numbers' in smell_types
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_feature_envy(self, analyzer, feature_envy_code):
        """Test feature envy smell detection."""
        with patch('builtins.open', mock_open(read_data=feature_envy_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'feature_envy' in smell_types
    
    @patch('builtins.open', mock_open())
    def test_analyze_file_smells_long_parameter_list(self, analyzer, long_parameter_list_code):
        """Test long parameter list smell detection."""
        with patch('builtins.open', mock_open(read_data=long_parameter_list_code)):
            test_file = Path('test.py')
            smells = analyzer._analyze_file_smells(test_file)
            
            smell_types = [smell['type'] for smell in smells]
            assert 'long_parameter_list' in smell_types
    
    @patch('builtins.open', side_effect=IOError())
    def test_analyze_file_smells_error(self, mock_open, analyzer):
        """Test file analysis with IO error."""
        test_file = Path('nonexistent.py')
        smells = analyzer._analyze_file_smells(test_file)
        assert smells == []
    
    @patch('builtins.open', mock_open(read_data=''))
    def test_analyze_file_smells_empty_file(self, analyzer):
        """Test analysis of empty file."""
        test_file = Path('empty.py')
        smells = analyzer._analyze_file_smells(test_file)
        assert smells == []
    
    def test_generate_smell_insights(self, analyzer):
        """Test smell insights generation."""
        from collections import Counter
        
        smells_by_type = Counter({
            'long_method': 5,
            'duplicate_code': 3,
            'magic_numbers': 8,
            'god_class': 1
        })
        
        severity_distribution = Counter({
            'high': 3,
            'medium': 8,
            'low': 8
        })
        
        hotspot_files = [
            ('file1.py', 15.5),
            ('file2.py', 12.3),
            ('file3.py', 8.7)
        ]
        
        insights = analyzer._generate_smell_insights(smells_by_type, severity_distribution, hotspot_files)
        
        assert 'top_smells' in insights
        assert 'severity_breakdown' in insights
        assert 'recommendations' in insights
        assert 'priority_actions' in insights
        
        # Check top smells
        assert len(insights['top_smells']) > 0
        assert insights['top_smells'][0][0] == 'magic_numbers'  # Most common
        
        # Check recommendations
        assert len(insights['recommendations']) > 0
        assert any('magic_numbers' in rec for rec in insights['recommendations'])
    
    @patch('builtins.open', mock_open())
    def test_analyze_integration(self, analyzer, long_method_code):
        """Test full analysis integration."""
        with patch('builtins.open', mock_open(read_data=long_method_code)):
            test_files = [Path('test1.py'), Path('test2.py')]
            result = analyzer.analyze(test_files)
            
            assert result is not None
            assert hasattr(result, 'total_count')
            assert hasattr(result, 'severity_score')
            assert hasattr(result, 'smells_by_type')
            assert hasattr(result, 'hotspot_files')
            assert hasattr(result, 'smells')
            
            assert result.total_count >= 0
            assert 0 <= result.severity_score <= 10
            assert isinstance(result.smells_by_type, dict)
            assert isinstance(result.hotspot_files, list)
            assert isinstance(result.smells, list)
    
    def test_empty_file_list(self, analyzer):
        """Test analysis with empty file list."""
        result = analyzer.analyze([])
        assert result is not None
        assert result.total_count == 0
        assert result.severity_score >= 0
    
    def test_javascript_smell_detection(self, analyzer):
        """Test JavaScript smell detection."""
        js_code = '''
function veryLongFunction() {
    // This function is too long
    let x = 1;
    let y = 2;
    ''' + '\n'.join([f'    let var{i} = {i};' for i in range(3, 60)]) + '''
    return x + y;
}

class DataProcessor {
    process(data1, data2, data3, data4, data5, data6, data7, data8, data9, data10) {
        // Too many parameters
        return data1 + data2;
    }
}
'''
        
        with patch('builtins.open', mock_open(read_data=js_code)):
            test_file = Path('test.js')
            smells = analyzer._analyze_file_smells(test_file)
            
            assert len(smells) > 0
            smell_types = [smell['type'] for smell in smells]
            # Should detect some smells in JavaScript code
            assert len(smell_types) > 0
    
    def test_smell_severity_distribution(self, analyzer):
        """Test that different smells have appropriate severities."""
        # Check that critical smells are properly categorized
        critical_smells = [pattern for pattern, config in analyzer.smell_patterns.items() 
                          if config['severity'] == 'critical']
        assert len(critical_smells) > 0
        
        # Check that we have smells of all severity levels
        severities = {config['severity'] for config in analyzer.smell_patterns.values()}
        assert 'high' in severities
        assert 'medium' in severities
        assert 'low' in severities
    
    def test_smell_pattern_thresholds(self, analyzer):
        """Test that smell patterns have reasonable thresholds."""
        long_method_threshold = analyzer.smell_patterns['long_method']['threshold']
        assert long_method_threshold > 20  # Should be reasonable threshold
        
        long_param_threshold = analyzer.smell_patterns['long_parameter_list']['threshold']
        assert long_param_threshold >= 4  # Reasonable parameter count threshold


if __name__ == '__main__':
    pytest.main([__file__])
