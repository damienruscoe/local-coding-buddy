#!/usr/bin/env python3
"""
Example: V4A Patch Format Usage

Demonstrates the V4A patch format and robust matching strategies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.v4a_patch import V4APatchApplier, validate_patch


def example_1_simple_update():
    """Example 1: Simple function update."""
    
    print("=" * 80)
    print("EXAMPLE 1: Simple Function Update")
    print("=" * 80)
    
    # Create test file
    original_code = '''def greet(name):
    return "Hello"

def farewell(name):
    return "Goodbye"
'''
    
    with open('test_simple.py', 'w') as f:
        f.write(original_code)
    
    # V4A patch to update greet function
    patch = '''*** Begin Patch
*** Update File: test_simple.py
@@ def greet @@
 def greet(name):
-    return "Hello"
+    return f"Hello, {name}!"
 
*** End Patch
'''
    
    print("Original code:")
    print(original_code)
    print("\nApplying patch...")
    print(patch)
    
    # Apply patch
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    for op in result['operations']:
        print(f"  - {op.action}: {op.file_path}")
        print(f"    Match strategy: {op.match_strategy}")
        print(f"    Line range: {op.line_range}")
    
    print("\nUpdated code:")
    with open('test_simple.py', 'r') as f:
        print(f.read())
    
    os.remove('test_simple.py')
    print()


def example_2_add_new_file():
    """Example 2: Adding a new file."""
    
    print("=" * 80)
    print("EXAMPLE 2: Add New File")
    print("=" * 80)
    
    patch = '''*** Begin Patch
*** Add File: test_new.py
+def fibonacci(n):
+    """Calculate nth Fibonacci number."""
+    if n <= 1:
+        return n
+    return fibonacci(n-1) + fibonacci(n-2)
+
+def factorial(n):
+    """Calculate factorial of n."""
+    if n <= 1:
+        return 1
+    return n * factorial(n-1)
*** End Patch
'''
    
    print("Applying patch to create new file...")
    print(patch)
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    
    if result['success']:
        print("\nNew file created:")
        with open('test_new.py', 'r') as f:
            print(f.read())
        os.remove('test_new.py')
    
    print()


def example_3_fuzzy_matching():
    """Example 3: Fuzzy matching with whitespace differences."""
    
    print("=" * 80)
    print("EXAMPLE 3: Fuzzy Matching (Whitespace Differences)")
    print("=" * 80)
    
    # Create file with different indentation
    original_code = '''def calculate(x, y):
        result = x + y
        return result
'''
    
    with open('test_fuzzy.py', 'w') as f:
        f.write(original_code)
    
    # Patch with slightly different whitespace
    patch = '''*** Begin Patch
*** Update File: test_fuzzy.py
@@ def calculate @@
 def calculate(x, y):
-    result = x + y
-    return result
+    result = x + y
+    print(f"Result: {result}")
+    return result
*** End Patch
'''
    
    print("Original code (extra indentation):")
    print(original_code)
    print("\nApplying patch with fuzzy matching...")
    
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    for op in result['operations']:
        print(f"  Match strategy: {op.match_strategy}")
    
    if result['success']:
        print("\nUpdated code:")
        with open('test_fuzzy.py', 'r') as f:
            print(f.read())
    
    os.remove('test_fuzzy.py')
    print()


def example_4_context_based_matching():
    """Example 4: Context-based matching in larger files."""
    
    print("=" * 80)
    print("EXAMPLE 4: Context-Based Matching")
    print("=" * 80)
    
    # Create larger file
    original_code = '''class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x):
        self.value += x
        return self.value
    
    def subtract(self, x):
        self.value -= x
        return self.value

class ScientificCalculator(Calculator):
    def power(self, exp):
        self.value = self.value ** exp
        return self.value
'''
    
    with open('test_context.py', 'w') as f:
        f.write(original_code)
    
    # Update specific class method using context
    patch = '''*** Begin Patch
*** Update File: test_context.py
@@ class ScientificCalculator @@
 class ScientificCalculator(Calculator):
     def power(self, exp):
-        self.value = self.value ** exp
+        """Raise value to power."""
+        self.value = self.value ** exp
         return self.value
*** End Patch
'''
    
    print("Original code:")
    print(original_code)
    print("\nApplying patch with context header...")
    
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    for op in result['operations']:
        print(f"  Match strategy: {op.match_strategy}")
        print(f"  Line range: {op.line_range}")
    
    if result['success']:
        print("\nUpdated code:")
        with open('test_context.py', 'r') as f:
            print(f.read())
    
    os.remove('test_context.py')
    print()


def example_5_error_handling():
    """Example 5: Error handling with suggestions."""
    
    print("=" * 80)
    print("EXAMPLE 5: Error Handling and Suggestions")
    print("=" * 80)
    
    original_code = '''def hello():
    return "Hi there!"
'''
    
    with open('test_error.py', 'w') as f:
        f.write(original_code)
    
    # Patch with incorrect code to match
    patch = '''*** Begin Patch
*** Update File: test_error.py
@@ def hello @@
 def hello():
-    return "Hello, World!"
+    return "Hi, World!"
*** End Patch
'''
    
    print("Original code:")
    print(original_code)
    print("\nAttempting to apply patch with wrong code...")
    
    applier = V4APatchApplier(verbose=True)
    result = applier.apply_patch(patch)
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    
    if not result['success']:
        print("\nErrors:")
        for error in result.get('errors', []):
            print(f"  - {error}")
        
        for op in result['operations']:
            if not op.success and op.suggestions:
                print("\nSuggestions for similar code:")
                for sug in op.suggestions:
                    print(f"\n  Line {sug['line']}:")
                    print(f"    Tokens matched: {sug['overlap_tokens']}")
                    print(f"    Context:")
                    for line in sug['context'].split('\n'):
                        print(f"      {line}")
    
    os.remove('test_error.py')
    print()


def example_6_validation():
    """Example 6: Validating patches before applying."""
    
    print("=" * 80)
    print("EXAMPLE 6: Patch Validation")
    print("=" * 80)
    
    valid_patch = '''*** Begin Patch
*** Add File: test.py
+def test():
+    pass
*** End Patch
'''
    
    invalid_patch = '''*** Begin Patch
*** Add File: test.py
This is not valid V4A format!
'''
    
    print("Validating patches before applying...\n")
    
    is_valid, error = validate_patch(valid_patch)
    print(f"Valid patch: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    is_valid, error = validate_patch(invalid_patch)
    print(f"\nInvalid patch: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    print()


if __name__ == "__main__":
    example_1_simple_update()
    example_2_add_new_file()
    example_3_fuzzy_matching()
    example_4_context_based_matching()
    example_5_error_handling()
    example_6_validation()
    
    print("=" * 80)
    print("All examples complete!")
    print("=" * 80)
