"""
Unit tests for V4A patch parser and applier.
"""

import pytest
import os
import tempfile
from orchestrator.v4a_patch import (
    V4APatchParser,
    V4APatchApplier,
    V4AAction,
    validate_patch
)


@pytest.fixture
def test_file():
    """Create a test file."""
    content = '''def greet(name):
    return "Hello"

def farewell(name):
    return "Goodbye"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        return f.name


DAMO = '''*** Begin Patch
*** Create File: my_module.py
+def add_two_numbers(a, b):
+    """Add two numbers."""
+    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
+        raise TypeError("Both inputs must be numbers.")
+    return a + b
*** End Patch

*** Begin Patch
*** Create File: test_my_module.py
+import pytest
+from my_module import add_two_numbers
+
+@pytest.mark.parametrize(
+    'test_input,expected',
+    [
+        (2, 3, 5),
+        (5, 2, 7),
+        (0, 0, 0),
+        (-1, 1, 0),
+        (-1, 1, 0),
+        (-1.1, 1.1, 0.0),
+        (5.5, -3.3, 2.2),
+        (3, "hello", pytest.raises(TypeError)),
+        ("hello", 3, pytest.raises(TypeError)),
+    ],
+)
+def test_add_two_numbers(test_input, expected):
+    assert add_two_numbers(test_input[0], test_input[1]) == expected
*** End Patch'''

def test_parse_DAMO():
    parser = V4APatchParser()
    hunks = parser.parse(DAMO)
    
    assert len(hunks) == 2

    assert hunks[0].action == V4AAction.ADD
    assert hunks[0].file_path == 'my_module.py'
    assert len(hunks[0].added_lines) == 5

    assert hunks[1].action == V4AAction.ADD
    assert hunks[1].file_path == 'test_my_module.py'
    assert len(hunks[1].added_lines) == 19


def test_parse_add_patch():
    """Test parsing Add File patches."""
    patch = '''*** Begin Patch
*** Add File: test.py
+def hello():
+    return "Hello"
*** End Patch
'''
    
    parser = V4APatchParser()
    hunks = parser.parse(patch)
    
    assert len(hunks) == 1
    assert hunks[0].action == V4AAction.ADD
    assert hunks[0].file_path == 'test.py'
    assert len(hunks[0].added_lines) == 2


def test_parse_update_patch():
    """Test parsing Update File patches."""
    patch = '''*** Begin Patch
*** Update File: test.py
@@ def greet @@
 def greet(name):
-    return "Hello"
+    return f"Hello, {name}!"
*** End Patch
'''
    
    parser = V4APatchParser()
    hunks = parser.parse(patch)
    
    assert len(hunks) == 1
    assert hunks[0].action == V4AAction.UPDATE
    assert hunks[0].file_path == 'test.py'
    assert hunks[0].context_header == '@@ def greet @@'
    assert len(hunks[0].removed_lines) == 1
    assert len(hunks[0].added_lines) == 1


def test_parse_delete_patch():
    """Test parsing Delete File patches."""
    patch = '''*** Begin Patch
*** Delete File: test.py
*** End Patch
'''
    
    parser = V4APatchParser()
    hunks = parser.parse(patch)
    
    assert len(hunks) == 1
    assert hunks[0].action == V4AAction.DELETE
    assert hunks[0].file_path == 'test.py'


def test_apply_add_patch():
    """Test applying Add File operation."""
    patch = '''*** Begin Patch
*** Add File: test_new.py
+def test():
+    pass
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    assert os.path.exists('test_new.py')
    
    with open('test_new.py', 'r') as f:
        content = f.read()
        assert 'def test()' in content
    
    os.remove('test_new.py')


def test_apply_update_exact_match(test_file):
    """Test applying update with exact match."""
    patch = f'''*** Begin Patch
*** Update File: {test_file}
@@ def greet @@
 def greet(name):
-    return "Hello"
+    return f"Hello, {{name}}!"
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    
    with open(test_file, 'r') as f:
        content = f.read()
        assert 'return f"Hello, {name}!"' in content
    
    os.remove(test_file)


def test_apply_update_fuzzy_match():
    """Test fuzzy matching with whitespace differences."""
    # Create file with different whitespace
    content = '''def calculate(x, y):
        result = x + y
        return result
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        test_file = f.name
    
    patch = f'''*** Begin Patch
*** Update File: {test_file}
@@ def calculate @@
 def calculate(x, y):
-    result = x + y
-    return result
+    result = x + y
+    print(result)
+    return result
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    assert result['operations'][0].match_strategy in ['exact', 'fuzzy']
    
    os.remove(test_file)


def test_apply_delete_patch(test_file):
    """Test applying Delete File operation."""
    patch = f'''*** Begin Patch
*** Delete File: {test_file}
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    assert not os.path.exists(test_file)


def test_failed_match_suggestions():
    """Test that failed matches provide suggestions."""
    content = '''def hello():
    return "Hi there!"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        test_file = f.name
    
    # Patch with wrong code to match
    patch = f'''*** Begin Patch
*** Update File: {test_file}
@@ def hello @@
 def hello():
-    return "Hello, World!"
+    return "Hi, World!"
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert not result['success']
    assert len(result['operations']) > 0
    assert result['operations'][0].suggestions is not None
    
    os.remove(test_file)


def test_dry_run_mode(test_file):
    """Test that dry run doesn't modify files."""
    original_content = open(test_file, 'r').read()
    
    patch = f'''*** Begin Patch
*** Update File: {test_file}
@@ def greet @@
 def greet(name):
-    return "Hello"
+    return "Hi"
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch, dry_run=True)
    
    # Check file wasn't modified
    new_content = open(test_file, 'r').read()
    assert original_content == new_content
    
    os.remove(test_file)


def test_validate_patch_valid():
    """Test validating a valid patch."""
    patch = '''*** Begin Patch
*** Add File: test.py
+def test():
+    pass
*** End Patch
'''
    
    is_valid, error = validate_patch(patch)
    assert is_valid
    assert error is None


def test_validate_patch_invalid():
    """Test validating an invalid patch."""
    patch = '''This is not a valid V4A patch'''
    
    is_valid, error = validate_patch(patch)
    assert not is_valid
    assert error is not None


def test_multiple_operations():
    """Test patch with multiple operations."""
    patch = '''*** Begin Patch
*** Add File: file1.py
+def func1():
+    pass

*** Add File: file2.py
+def func2():
+    pass
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    assert len(result['operations']) == 2
    
    os.remove('file1.py')
    os.remove('file2.py')


def test_context_header_matching():
    """Test matching using context headers."""
    content = '''class Calculator:
    def add(self, x, y):
        return x + y

class ScientificCalculator:
    def add(self, x, y):
        return x + y
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        test_file = f.name
    
    # Update specific class using context header
    patch = f'''*** Begin Patch
*** Update File: {test_file}
@@ class ScientificCalculator @@
 class ScientificCalculator:
     def add(self, x, y):
-        return x + y
+        result = x + y
+        return result
*** End Patch
'''
    
    applier = V4APatchApplier()
    result = applier.apply_patch(patch)
    
    assert result['success']
    
    # Verify only ScientificCalculator was updated
    with open(test_file, 'r') as f:
        lines = f.readlines()
        # First add should still be simple
        assert any('class Calculator' in line for line in lines)
        # Second add should have the change
        scientific_start = next(i for i, l in enumerate(lines) if 'ScientificCalculator' in l)
        assert 'result = x + y' in ''.join(lines[scientific_start:])
    
    os.remove(test_file)
