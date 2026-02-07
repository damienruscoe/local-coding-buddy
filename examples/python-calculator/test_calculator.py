"""
Tests for calculator module.
"""
import unittest
from calculator import add, subtract


class TestCalculator(unittest.TestCase):
    """Test calculator functions."""
    
    def test_add_positive_numbers(self):
        """Test adding positive numbers."""
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(10, 20), 30)
    
    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        self.assertEqual(add(-5, -3), -8)
        self.assertEqual(add(-10, 5), -5)
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        self.assertEqual(subtract(10, 5), 5)
        self.assertEqual(subtract(20, 8), 12)
    
    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        self.assertEqual(subtract(-5, -3), -2)
        self.assertEqual(subtract(10, -5), 15)


if __name__ == '__main__':
    unittest.main()
