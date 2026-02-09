# Quick Start Guide

Get started with the enhanced local-coding-buddy in 5 minutes!

## 1. Installation (2 minutes)

```bash
# Install dependencies
pip install -r requirements-orchestrator.txt

# Optional: If you want to use tree-sitter strategy (recommended)
pip install tree-sitter tree-sitter-python tree-sitter-cpp
```

## 2. Configuration (1 minute)

```bash
# Copy example config
cp config/config.yaml.example config/config.yaml

# Edit config (optional - defaults are good)
nano config/config.yaml
```

Key settings:
```yaml
# Choose your strategy (change this one line!)
context_extraction_strategy: "tree_sitter"  # or "ast" or "heuristic"
```

## 3. Try the Examples (2 minutes)

### Compare Extraction Strategies
```bash
python examples/compare_strategies.py
```

This will:
- Create a sample Python file
- Run all three extraction strategies
- Show you the differences in output
- Help you choose the best strategy

### Try V4A Patches
```bash
python examples/v4a_patch_examples.py
```

This will:
- Demonstrate all V4A operations (add, update, delete)
- Show exact, fuzzy, and context-based matching
- Display error handling with suggestions

## 4. Use in Your Code

### Extract Context
```python
from orchestrator.context_extractor import extract_context

context = extract_context(
    file_path="your_file.py",
    task_description="Add error handling to parse_data function",
    strategy="tree_sitter"
)

print(f"Found {len(context.relevant_sections)} relevant sections")
print(f"Symbols: {context.all_symbols}")
```

### Apply V4A Patches
```python
from orchestrator.v4a_patch import V4APatchApplier

patch = '''*** Begin Patch
*** Update File: your_file.py
@@ def parse_data @@
 def parse_data(data):
+    if not data:
+        raise ValueError("Data cannot be empty")
     return json.loads(data)
*** End Patch
'''

applier = V4APatchApplier()
result = applier.apply_patch(patch)

if result['success']:
    print("Patch applied!")
else:
    print(f"Errors: {result['errors']}")
```

### Complete Workflow
```python
from orchestrator.implementer_workflow import run_implementer_stage

task = {
    'description': 'Add input validation to process_user_data',
    'acceptance_criteria': [
        'Check user_data is not None',
        'Validate email format',
        'Raise ValueError on invalid input'
    ]
}

result = run_implementer_stage(
    task=task,
    file_path='app/user_handler.py',
    agents_client=your_agent_client
)

print(f"Success: {result['success']}")
```

## 5. Switch Strategies

To try different extraction strategies:

### Option 1: Config File
Edit `config/config.yaml`:
```yaml
context_extraction_strategy: "ast"  # Change this line
```

### Option 2: Code
```python
from orchestrator.context_extractor import extract_context

# Tree-sitter (recommended for multi-language)
context = extract_context(file, task, strategy="tree_sitter")

# AST (best for Python)
context = extract_context(file, task, strategy="ast")

# Heuristic (fast, any language)
context = extract_context(file, task, strategy="heuristic")
```

## Troubleshooting

### "Tree-sitter not found"
```bash
pip install tree-sitter tree-sitter-python
```

### "Could not locate code to replace"
Enable verbose mode to see matching attempts:
```yaml
# In config.yaml
patch_verbose: true
```

Or in code:
```python
applier = V4APatchApplier(verbose=True)
```

### Strategy Fails
Try a different strategy:
```yaml
# In config.yaml
context_extraction_strategy: "heuristic"  # Most robust fallback
```

## Next Steps

1. **Read the full README**: `README.md` has detailed documentation
2. **Check examples**: `examples/` has more use cases
3. **Run tests**: `pytest orchestrator/tests/`
4. **Read the changelog**: `CHANGELOG.md` for what changed

## Strategy Recommendations

| Use Case | Recommended Strategy | Why |
|----------|---------------------|-----|
| Python projects | `ast` | Most accurate, built-in |
| Multi-language | `tree_sitter` | Supports Python + C++ |
| Quick prototype | `heuristic` | No dependencies, fast |
| Large files | `tree_sitter` or `ast` | Better symbol extraction |
| Unknown language | `heuristic` | Works for anything |

## Common Patterns

### Validate Before Apply
```python
# Always validate first!
result = applier.apply_patch(patch, dry_run=True)

if result['success']:
    # Safe to apply
    applier.apply_patch(patch, dry_run=False)
else:
    # Fix errors first
    handle_errors(result)
```

### Extract Minimal Context
```python
# For small changes, reduce context size
extractor = ContextExtractor(max_context_lines=25)
context = extractor.extract_for_task(file, task)
```

### Handle Errors with Feedback
```python
for attempt in range(3):
    patch = generate_patch(context, feedback)
    result = apply_patch(patch)
    
    if result['success']:
        break
    
    # Extract suggestions for next attempt
    feedback = result['operations'][0].suggestions
```

## You're Ready!

You now have:
- ✅ Context extraction working
- ✅ V4A patch format understanding
- ✅ Examples to learn from
- ✅ Strategy selection knowledge

Start building! 🚀
