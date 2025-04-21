import pytest

from app.utils.helpers import format_number, format_percentage, format_market_cap

class TestFormatNumber:
    """Tests for the format_number function"""
    
    def test_format_number_default_decimal_places(self):
        """Test format_number with default decimal places (2)"""
        value = 1234.5678
        formatted = format_number(value)
        assert formatted == "1,234.57"
    
    def test_format_number_custom_decimal_places(self):
        """Test format_number with custom decimal places"""
        value = 1234.5678
        formatted = format_number(value, decimal_places=3)
        assert formatted == "1,234.568"
    
    def test_format_number_no_decimal_places(self):
        """Test format_number with no decimal places"""
        value = 1234.5678
        formatted = format_number(value, decimal_places=0)
        assert formatted == "1,235"  # Should round up
    
    def test_format_number_negative_value(self):
        """Test format_number with a negative value"""
        value = -1234.5678
        formatted = format_number(value)
        assert formatted == "-1,234.57"
    
    def test_format_number_zero(self):
        """Test format_number with zero"""
        value = 0
        formatted = format_number(value)
        assert formatted == "0.00"
    
    def test_format_number_large_value(self):
        """Test format_number with a large value"""
        value = 1234567890.12
        formatted = format_number(value)
        assert formatted == "1,234,567,890.12"

class TestFormatPercentage:
    """Tests for the format_percentage function"""
    
    def test_format_percentage_default_decimal_places(self):
        """Test format_percentage with default decimal places (2)"""
        value = 0.12345
        formatted = format_percentage(value)
        assert formatted == "12.35%"  # 12.345% rounded to 2 decimal places
    
    def test_format_percentage_custom_decimal_places(self):
        """Test format_percentage with custom decimal places"""
        value = 0.12345
        formatted = format_percentage(value, decimal_places=3)
        assert formatted == "12.345%"
    
    def test_format_percentage_no_decimal_places(self):
        """Test format_percentage with no decimal places"""
        value = 0.12345
        formatted = format_percentage(value, decimal_places=0)
        assert formatted == "12%"  # Should round to nearest
    
    def test_format_percentage_negative_value(self):
        """Test format_percentage with a negative value"""
        value = -0.12345
        formatted = format_percentage(value)
        assert formatted == "-12.35%"
    
    def test_format_percentage_zero(self):
        """Test format_percentage with zero"""
        value = 0
        formatted = format_percentage(value)
        assert formatted == "0.00%"
    
    def test_format_percentage_large_value(self):
        """Test format_percentage with a value greater than 1"""
        value = 1.5
        formatted = format_percentage(value)
        assert formatted == "150.00%"

class TestFormatMarketCap:
    """Tests for the format_market_cap function"""
    
    def test_format_market_cap_billions(self):
        """Test format_market_cap with a value in billions"""
        value = 2000000000000  # 2 trillion
        formatted = format_market_cap(value)
        assert formatted == "$2000.00B"
    
    def test_format_market_cap_millions(self):
        """Test format_market_cap with a value in millions"""
        value = 750000000  # 750 million
        formatted = format_market_cap(value)
        assert formatted == "$750.00M"
    
    def test_format_market_cap_thousands(self):
        """Test format_market_cap with a value less than 1 million"""
        value = 500000  # 500 thousand
        formatted = format_market_cap(value)
        assert formatted == "$500000.00"
    
    def test_format_market_cap_small_value(self):
        """Test format_market_cap with a small value"""
        value = 1000  # 1 thousand
        formatted = format_market_cap(value)
        assert formatted == "$1000.00"
    
    def test_format_market_cap_zero(self):
        """Test format_market_cap with zero"""
        value = 0
        formatted = format_market_cap(value)
        assert formatted == "$0.00" 