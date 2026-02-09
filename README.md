# Local AI Coding Buddy - Enhanced Edition

A fully autonomous local AI coding assistant with **robust context extraction** and **industry-standard V4A patch format**.

## 🎯 What's New in This Version

### 1. **Intelligent Context Extraction** (No More Sending Entire Files!)
- **Three extraction strategies** you can switch with one line of code:
  - **Tree-sitter** (recommended): Language-agnostic, works for Python & C++
  - **AST**: Python-specific, most accurate for Python files
  - **Heuristic**: Fast regex-based, works for any language

- **Smart context selection**: Only sends relevant code sections to the LLM
- **Deterministic**: No LLM needed for extraction - fast and predictable
- **Keyword matching**: Finds code related to the task automatically

### 2. **V4A Patch Format** (No More Line Number Hell!)
- Uses **OpenAI's V4A format** - the same format GPT models are trained on
- **Context-based matching**: Uses function/class names, not brittle line numbers
- **Layered matching strategies**:
  1. Exact match
  2. Fuzzy match (handles whitespace differences)
  3. Context-header search (finds code within specific classes/functions)

- **Detailed error feedback**: When a patch fails, get suggestions for similar code
- **Validation before apply**: Dry-run mode catches issues before modifying files

### 3. **Easy Strategy Switching**
Change extraction strategy with **one line** in `config/config.yaml`:
```yaml
context_extraction_strategy: "tree_sitter"  # or "ast" or "heuristic"
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd local-coding-buddy-updated

# Install dependencies
pip install -r requirements-orchestrator.txt

# Configure
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml - set your preferences
```

### Try the Examples

```bash
# Compare all three context extraction strategies
python examples/compare_strategies.py

# See V4A patch format in action
python examples/v4a_patch_examples.py
```

## 📖 How It Works

### Context Extraction Flow

```
User Request: "Add fibonacci function"
    ↓
Context Extractor (configurable strategy)
    ↓
Extracts relevant code sections:
  - Functions matching keywords ("fibonacci")
  - Related classes/modules
  - Surrounding context (5-10 lines)
    ↓
Sends ONLY relevant code to LLM
(Not entire 1000-line file!)
```

### V4A Patch Application Flow

```
LLM generates V4A patch
    ↓
Parse patch into structured operations
    ↓
Validate (dry-run)
    ├─ Success → Apply for real
    └─ Failure → Detailed error + suggestions
           ↓
       Retry with feedback
```

## 🎨 Usage Examples

### Example 1: Using Context Extractor Directly

```python
from orchestrator.context_extractor import extract_context

# Extract context for a task
context = extract_context(
    file_path="my_module.py",
    task_description="Add a fibonacci function",
    strategy="tree_sitter"  # Easy to switch!
)

print(f"Strategy used: {context.strategy}")
print(f"Found symbols: {context.all_symbols}")
print(f"Relevant sections: {len(context.relevant_sections)}")
```

### Example 2: Applying V4A Patches

```python
from orchestrator.v4a_patch import V4APatchApplier

patch = '''*** Begin Patch
*** Update File: calculator.py
@@ class Calculator @@
 class Calculator:
     def add(self, a, b):
-        return a + b
+        """Add two numbers with logging."""
+        result = a + b
+        print(f"Adding {a} + {b} = {result}")
+        return result
*** End Patch
'''

applier = V4APatchApplier(verbose=True)
result = applier.apply_patch(patch)

if result['success']:
    print("Patch applied successfully!")
else:
    print(f"Errors: {result['errors']}")
    print(f"Suggestions: {result['operations'][0].suggestions}")
```

### Example 3: Complete Workflow

```python
from orchestrator.implementer_workflow import run_implementer_stage

task = {
    'description': 'Add error handling to the divide function',
    'acceptance_criteria': ['Handle division by zero', 'Return None on error']
}

result = run_implementer_stage(
    task=task,
    file_path='calculator.py',
    agents_client=my_agent_client
)

print(f"Success: {result['success']}")
print(f"Attempts: {result['attempt']}")
print(f"Strategy: {result['context_strategy']}")
```

## 🔧 Configuration

### config/config.yaml

```yaml
# STRATEGY SELECTION (change this one line!)
context_extraction_strategy: "tree_sitter"  # tree_sitter | ast | heuristic

# Context settings
max_context_lines: 50
small_file_threshold: 5120  # Files <5KB sent in full

# Patch settings
patch_verbose: false  # Enable for debugging

# Workflow settings
max_retries: 3
enable_refining: false
coverage_threshold: 80.0
```

## 📊 Strategy Comparison

| Strategy | Languages | Accuracy | Speed | Dependencies |
|----------|-----------|----------|-------|--------------|
| **tree_sitter** | Python, C++ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | tree-sitter libs |
| **ast** | Python only | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Built-in |
| **heuristic** | Any | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | None |

**Recommendation**: Use `tree_sitter` for most cases. It's language-agnostic and highly accurate.

## 🎯 Key Improvements Over Original

### Problem 1: Context Explosion
**Before**: Send entire file to LLM (1000+ lines)
**After**: Send only 50-100 lines of relevant code

### Problem 2: Line Numbers Don't Work
**Before**: LLM generates `@@ -0,0 +1,5 @@` but meant `@@ -0,0 +1,3 @@`
**After**: V4A format uses code context: `@@ class MyClass @@`

### Problem 3: No Context for Implementer
**Before**: Implementer doesn't know if file exists or where to insert code
**After**: Rich context includes file existence, symbols, and insertion points

### Problem 4: Brittle Patch Application
**Before**: `patch` command fails on minor differences
**After**: Layered matching (exact → fuzzy → context-based)

### Problem 5: Hard to Debug
**Before**: "Malformed patch" with no hints
**After**: Detailed suggestions showing similar code locations

## 🧪 Testing

Run the example scripts to see everything in action:

```bash
# Test context extraction
python examples/compare_strategies.py

# Test V4A patches
python examples/v4a_patch_examples.py

# Run unit tests
pytest orchestrator/tests/
```

## 🏗️ Architecture

```
orchestrator/
├── context_extractor.py       # Three extraction strategies
├── v4a_patch.py               # V4A parser and applier
├── implementer_workflow.py    # Integration layer
└── tests/                     # Unit tests

config/
└── config.yaml                # Easy strategy switching

examples/
├── compare_strategies.py      # Compare extraction methods
└── v4a_patch_examples.py      # V4A format examples
```

## 🔍 How Context Extraction Works

### Tree-sitter Strategy (Recommended)
```python
# Uses tree-sitter to parse code
tree = parser.parse(content)

# Find all functions/classes
symbols = extract_symbols(tree)

# Match to task keywords
relevant = match_keywords(symbols, "fibonacci")

# Extract with surrounding context
return context_sections
```

### AST Strategy (Python)
```python
# Parse Python AST
tree = ast.parse(content)

# Walk AST nodes
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # Extract function details
        symbols.append(...)

# Match and extract context
```

### Heuristic Strategy (Fallback)
```python
# Simple regex matching
for line in lines:
    if keyword in line:
        # Extract surrounding lines
        context = lines[i-10:i+10]
```

## 🎓 Best Practices

### 1. Choose the Right Strategy
- **Python projects**: `ast` (most accurate)
- **Multi-language**: `tree_sitter` (supports Python + C++)
- **Quick prototyping**: `heuristic` (no dependencies)

### 2. Tune Context Size
```yaml
# More context = better accuracy, higher token cost
max_context_lines: 50  # Default: good balance

# For complex refactors
max_context_lines: 100

# For simple changes
max_context_lines: 25
```

### 3. Use Validation
```python
# Always validate patches before applying
result = applier.apply_patch(patch, dry_run=True)

if result['success']:
    # Safe to apply
    applier.apply_patch(patch, dry_run=False)
else:
    # Review errors and retry
    handle_errors(result)
```

### 4. Enable Verbose Mode for Debugging
```yaml
patch_verbose: true  # See detailed matching info
```

## 🐛 Troubleshooting

### "Tree-sitter not found"
```bash
pip install tree-sitter tree-sitter-python tree-sitter-cpp
```

### "Could not locate code to replace"
- Check the V4A patch format is correct
- Enable `patch_verbose: true` to see matching attempts
- Review suggestions in error output
- Ensure context headers match actual code

### "Strategy X failed"
```yaml
# Switch to fallback strategy
context_extraction_strategy: "heuristic"
```

## 📚 Additional Resources

- **V4A Format Spec**: See `orchestrator/v4a_patch.py` docstring
- **Context Extraction**: See `orchestrator/context_extractor.py` docstring
- **Examples**: `examples/` directory

## 🤝 Contributing

When contributing:
1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Run `black` for formatting

## 📝 License

[Your chosen license]

## 🎉 Summary

This enhanced version solves the core problems:
1. ✅ **No more sending entire files** - intelligent context extraction
2. ✅ **No more line number errors** - V4A format uses code context
3. ✅ **Easy to switch strategies** - one line of config
4. ✅ **Robust patch application** - layered matching with fallbacks
5. ✅ **Detailed error feedback** - suggestions when patches fail

The implementer agent now has the context it needs, and the infrastructure can reliably apply its output.

**Ready to use!** 🚀
