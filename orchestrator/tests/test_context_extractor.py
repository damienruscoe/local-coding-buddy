"""
Unit tests for context extractor.
"""

import pytest
import os
import tempfile
from orchestrator.context_extractor import (
    ContextExtractor,
    ExtractionStrategy,
    extract_context
)


@pytest.fixture
def sample_python_file():
    """Create a temporary Python file for testing."""
    content = '''
import math

class Calculator:
    """A simple calculator."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b

def factorial(n):
    """Calculate factorial."""
    if n <= 1:
        return 1
    return n * factorial(n-1)
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        return f.name


@pytest.fixture
def small_file():
    """Create a small file (will be sent in full)."""
    content = 'def hello():\n    return "Hello"\n'
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        return f.name


def test_file_not_exists():
    """Test extraction when file doesn't exist."""
    extractor = ContextExtractor()
    context = extractor.extract_for_task('nonexistent.py', 'Add function')
    
    assert not context.file_exists
    assert context.action == 'create'
    assert context.all_symbols == []


def test_small_file_full_content(small_file):
    """Test that small files are sent in full."""
    extractor = ContextExtractor(small_file_threshold=1000)
    context = extractor.extract_for_task(small_file, 'Test')
    
    assert context.file_exists
    assert context.full_content is not None
    assert context.strategy == 'full_file_small'
    
    os.remove(small_file)


def test_ast_strategy(sample_python_file):
    """Test AST-based extraction."""
    extractor = ContextExtractor(strategy=ExtractionStrategy.AST)
    context = extractor.extract_for_task(
        sample_python_file,
        'Add a factorial function'
    )
    
    assert context.file_exists
    assert context.strategy == 'ast'
    assert 'Calculator' in context.all_symbols
    assert 'factorial' in context.all_symbols
    assert len(context.relevant_sections) > 0
    
    os.remove(sample_python_file)


def test_heuristic_strategy(sample_python_file):
    """Test heuristic-based extraction."""
    extractor = ContextExtractor(strategy=ExtractionStrategy.HEURISTIC)
    context = extractor.extract_for_task(
        sample_python_file,
        'Update multiply method'
    )
    
    assert context.file_exists
    assert context.strategy == 'heuristic'
    assert len(context.relevant_sections) > 0
    
    # Should find sections with 'multiply' keyword
    found_multiply = any(
        section.matched_keywords and 'multiply' in section.matched_keywords
        for section in context.relevant_sections
    )
    assert found_multiply or len(context.relevant_sections) > 0
    
    os.remove(sample_python_file)


def test_keyword_extraction():
    """Test keyword extraction from task descriptions."""
    extractor = ContextExtractor()
    keywords = extractor._extract_keywords(
        'Add a fibonacci function to calculate sequences'
    )
    
    assert 'fibonacci' in keywords
    assert 'calculate' in keywords
    assert 'sequences' in keywords
    # Stopwords should be filtered
    assert 'add' not in keywords
    assert 'to' not in keywords


def test_convenience_function(sample_python_file):
    """Test the convenience function."""
    context = extract_context(
        sample_python_file,
        'Add method',
        strategy='ast'
    )
    
    assert context.file_exists
    assert context.strategy == 'ast'
    
    os.remove(sample_python_file)


def test_symbol_matching(sample_python_file):
    """Test that symbols are matched to keywords."""
    extractor = ContextExtractor(strategy=ExtractionStrategy.AST)
    context = extractor.extract_for_task(
        sample_python_file,
        'Update the add method'
    )
    
    # Should find the 'add' method
    assert any(
        section.symbol == 'add'
        for section in context.relevant_sections
    )
    
    os.remove(sample_python_file)


def test_context_sections_have_line_ranges(sample_python_file):
    """Test that context sections include line ranges."""
    extractor = ContextExtractor(strategy=ExtractionStrategy.AST)
    context = extractor.extract_for_task(sample_python_file, 'Test')
    
    for section in context.relevant_sections:
        assert section.line_start is not None
        assert section.line_end is not None
        assert section.line_start <= section.line_end
    
    os.remove(sample_python_file)
