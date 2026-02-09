#!/usr/bin/env python3
"""
Example: Compare Context Extraction Strategies

This script demonstrates all three context extraction strategies
and compares their output.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.context_extractor import (
    ContextExtractor,
    ExtractionStrategy
)


def create_sample_file():
    """Create a sample Python file for testing."""
    sample_code = '''
import math

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result
    
    def fibonacci(self, n):
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        return self.fibonacci(n-1) + self.fibonacci(n-2)

def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n-1)

def main():
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 7))
    print(factorial(5))
'''
    
    with open('sample_calculator.py', 'w') as f:
        f.write(sample_code)
    
    return 'sample_calculator.py'


def compare_strategies():
    """Compare all three extraction strategies."""
    
    # Create sample file
    file_path = create_sample_file()
    task = "Add a function to calculate Fibonacci numbers"
    
    print("=" * 80)
    print("CONTEXT EXTRACTION STRATEGY COMPARISON")
    print("=" * 80)
    print(f"\nFile: {file_path}")
    print(f"Task: {task}")
    print("\n")
    
    strategies = [
        ExtractionStrategy.TREE_SITTER,
        ExtractionStrategy.AST,
        ExtractionStrategy.HEURISTIC
    ]
    
    for strategy in strategies:
        print("=" * 80)
        print(f"STRATEGY: {strategy.value.upper()}")
        print("=" * 80)
        
        try:
            extractor = ContextExtractor(strategy=strategy)
            context = extractor.extract_for_task(file_path, task)
            
            print(f"Strategy used: {context.strategy}")
            print(f"File exists: {context.file_exists}")
            print(f"Action: {context.action}")
            print(f"Total lines: {context.total_lines}")
            print(f"\nAll symbols found: {context.all_symbols}")
            
            if context.relevant_sections:
                print(f"\nRelevant sections: {len(context.relevant_sections)}")
                for i, section in enumerate(context.relevant_sections, 1):
                    print(f"\n--- Section {i} ---")
                    print(f"Lines: {section.line_start}-{section.line_end}")
                    if section.symbol:
                        print(f"Symbol: {section.symbol} ({section.symbol_type})")
                    if section.matched_keywords:
                        print(f"Matched keywords: {section.matched_keywords}")
                    print(f"\nCode preview (first 200 chars):")
                    print(section.lines[:200] + "..." if len(section.lines) > 200 else section.lines)
            
            print("\n")
            
        except Exception as e:
            print(f"ERROR: {e}")
            print("\n")
    
    # Cleanup
    os.remove(file_path)
    print("=" * 80)
    print("Comparison complete!")
    print("=" * 80)


def demonstrate_strategy_switching():
    """Show how easy it is to switch strategies."""
    
    print("\n" + "=" * 80)
    print("DEMONSTRATING EASY STRATEGY SWITCHING")
    print("=" * 80)
    
    print("""
To switch context extraction strategies, you only need to change ONE line:

In config/config.yaml:
    
    # Option 1: Use tree-sitter (recommended, language-agnostic)
    context_extraction_strategy: "tree_sitter"
    
    # Option 2: Use AST (Python-only, most accurate for Python)
    context_extraction_strategy: "ast"
    
    # Option 3: Use heuristic (works for any language, fast)
    context_extraction_strategy: "heuristic"

Or in code:

    # Method 1: Using the convenience function
    from orchestrator.context_extractor import extract_context
    
    context = extract_context(
        file_path="my_file.py",
        task_description="Add a function",
        strategy="tree_sitter"  # Change this one parameter!
    )
    
    # Method 2: Using the class
    from orchestrator.context_extractor import ContextExtractor, ExtractionStrategy
    
    extractor = ContextExtractor(
        strategy=ExtractionStrategy.TREE_SITTER  # Change this!
    )
    context = extractor.extract_for_task(file_path, task)
""")


if __name__ == "__main__":
    compare_strategies()
    demonstrate_strategy_switching()
