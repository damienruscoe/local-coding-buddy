# User Guide

Complete guide to using the Local AI Coding Buddy effectively.

## Table of Contents

1. [Understanding the System](#understanding-the-system)
2. [Writing Good Requests](#writing-good-requests)
3. [Working with Existing Code](#working-with-existing-code)
4. [Configuration Options](#configuration-options)
5. [Best Practices](#best-practices)
6. [Advanced Usage](#advanced-usage)

## Understanding the System

### What It Does

The coding buddy:
- ✅ Implements well-defined features
- ✅ Writes tests for new code
- ✅ Refactors existing code
- ✅ Fixes bugs with known symptoms
- ✅ Adds documentation

### What It Doesn't Do

The coding buddy does NOT:
- ❌ Redesign architecture
- ❌ Make subjective design decisions
- ❌ Interact with external services
- ❌ Deploy code
- ❌ Debug complex runtime issues

### How It Works

1. **You provide**: A clear coding request
2. **System plans**: Breaks request into tasks
3. **Tests generated**: Defines success criteria
4. **Code written**: Implements each task
5. **Tests run**: Validates correctness
6. **Changes committed**: On success (if auto-commit enabled)

## Writing Good Requests

### Request Structure

A good request is:
- **Specific**: "Add a login function" not "improve security"
- **Scoped**: One feature at a time
- **Testable**: Can be verified with tests
- **Self-contained**: Doesn't depend on external state

### Examples

**❌ Bad Requests**:
```
"Make the app better"
"Fix all bugs"
"Optimize everything"
"Add AI features"
```

**✅ Good Requests**:
```
"Add a function to validate email addresses with regex"
"Implement binary search on sorted arrays with unit tests"
"Add error handling to the database connection function"
"Extract duplicate validation logic into a helper function"
```

### Request Templates

#### Adding a Feature
```
Add [feature name] that [specific behavior].
Include unit tests covering [scenarios].
```

Example:
```
Add a password strength validator that checks for:
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- At least one special character
Include unit tests covering valid and invalid passwords.
```

#### Refactoring
```
Refactor [component] to [improvement goal].
Ensure all existing tests still pass.
```

Example:
```
Refactor the User class to separate validation logic into 
a UserValidator class. Ensure all existing tests still pass.
```

#### Bug Fixes
```
Fix [specific bug] where [symptoms].
Expected behavior: [correct behavior].
```

Example:
```
Fix the divide_by_zero error in the calculate function where 
division by zero causes a crash. Expected behavior: return 
None and log a warning.
```

#### Documentation
```
Add [type of documentation] to [scope].
Include [specific elements].
```

Example:
```
Add docstrings to all public functions in the utils module.
Include parameter types, return types, and usage examples.
```

## Working with Existing Code

### Scanning Your Codebase

Before your first request:

```bash
docker-compose exec orchestrator python -m orchestrator.main scan \
  --project /workspace
```

This generates summaries without reading all code into context.

### Making Changes

The system handles existing codebases by:

1. **Scanning**: Building a symbol index
2. **Filtering**: Showing only relevant context to agents
3. **Minimal diffs**: Changing only what's needed
4. **Testing**: Ensuring no regressions

### Best Practices for Existing Code

1. **Start with small changes**: Don't try to refactor everything at once
2. **Have good tests**: Existing tests help validate changes
3. **Use branches**: Run on feature branches first
4. **Review carefully**: Check diffs before accepting

## Configuration Options

### config/config.yaml

```yaml
# How many times to retry failed tasks
max_retries: 3

# Enable code refactoring stage (slower but cleaner code)
enable_refining: false

# Minimum test coverage percentage
coverage_threshold: 80.0

# Maximum time for agent calls (seconds)
agent_timeout: 300

# Maximum time for test execution (seconds)
test_timeout: 300

# Path to model file
model_path: /models/base-model.gguf

# Model context window size (larger = more context, slower)
context_size: 4096

# Maximum tokens to generate
max_tokens: 2048

# Sampling temperature (lower = more deterministic)
temperature: 0.7

# Auto-commit successful changes
auto_commit: false
```

### When to Adjust

**Increase `max_retries`** if:
- Tasks occasionally fail for timing reasons
- Model needs more attempts

**Enable `refining`** if:
- Code quality is more important than speed
- Working on production code

**Lower `coverage_threshold`** if:
- Working with legacy code
- Tests are difficult to write

**Increase `agent_timeout`** if:
- Using large context windows
- Model is slow

**Adjust `temperature`**:
- Lower (0.3-0.5): More deterministic, better for structured output
- Higher (0.7-0.9): More creative, better for diverse solutions

## Best Practices

### 1. Version Control

Always work with git:

```bash
# Before running coding buddy
git status
git commit -am "Checkpoint before AI changes"

# After running
git diff
git log
```

### 2. Incremental Development

Make one change at a time:

```bash
# ✅ Good
--request "Add input validation to login function"

# ❌ Too much
--request "Add validation, logging, and error handling to all functions"
```

### 3. Review Everything

Even with auto-commit off, review changes:

```bash
# View diff
git diff HEAD

# Review file-by-file
git diff HEAD -- path/to/file.py
```

### 4. Test Coverage

Aim for high coverage:

```bash
# Check coverage manually
docker-compose exec orchestrator bash
cd /workspace
pytest --cov=. --cov-report=term
```

### 5. Clear Specifications

The more specific you are, the better results:

```bash
# Vague
--request "improve error handling"

# Specific
--request "wrap database calls in try-except blocks and log errors to logging.error"
```

## Advanced Usage

### Custom Quality Gates

Edit `orchestrator/validators.py` to add custom checks:

```python
def _custom_check(self) -> List[str]:
    """Your custom validation."""
    issues = []
    # Add your logic
    return issues
```

### Multi-Language Projects

The system supports mixing Python and C++:

```
project/
├── src/           # C++ source
├── python/        # Python source
├── tests/         # Tests for both
└── CMakeLists.txt # C++ build
```

### Batch Operations

Process multiple requests:

```bash
#!/bin/bash
requests=(
  "Add logging to main.py"
  "Add docstrings to utils.py"
  "Add type hints to models.py"
)

for req in "${requests[@]}"; do
  docker-compose exec orchestrator python -m orchestrator.main run \
    --project /workspace \
    --request "$req"
done
```

### Integration with CI/CD

Run as part of automation:

```yaml
# .github/workflows/coding-buddy.yml
name: AI Code Review
on: [pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run coding buddy
        run: |
          docker-compose up -d
          docker-compose exec -T orchestrator python -m orchestrator.main run \
            --project /workspace \
            --request "${{ github.event.pull_request.body }}"
```

### Custom Agents

Add your own agent types in `agents/agent_prompts.py`:

```python
CUSTOM_AGENT_PROMPT = """
You are a [role]. Your task is to [responsibility].

Guidelines:
- [guideline 1]
- [guideline 2]

Output format:
[expected format]
"""

def get_system_prompt(agent_type: str) -> str:
    prompts = {
        # ... existing agents ...
        'custom': CUSTOM_AGENT_PROMPT,
    }
    return prompts.get(agent_type, "...")
```

### Monitoring Performance

Track metrics over time:

```bash
# Extract metrics from state files
find /state -name "workflow_state.json" -exec jq '.metrics' {} \;

# Aggregate
grep "Task completed" /state/orchestrator.log | wc -l
```

## Common Workflows

### Adding a New Feature

```bash
# 1. Create feature branch
cd your-project
git checkout -b feature/new-feature

# 2. Run coding buddy
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add [feature description]"

# 3. Review changes
git diff main

# 4. Merge if satisfied
git checkout main
git merge feature/new-feature
```

### Fixing a Bug

```bash
# 1. Reproduce bug and document
# 2. Request fix with specific symptoms
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Fix bug where [symptoms]. Expected: [correct behavior]"

# 3. Verify fix
run-tests

# 4. Commit
git commit -am "Fix: [bug description]"
```

### Code Cleanup

```bash
# Enable refining for cleanup tasks
# Edit config/config.yaml: enable_refining: true

# Run cleanup
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Refactor [module] to improve readability"
```

## Tips and Tricks

### Faster Iterations

- Use smaller models (7B vs 13B)
- Lower quantization (Q2/Q3 vs Q4/Q5)
- Reduce context_size
- Disable refining

### Better Code Quality

- Enable refining
- Raise coverage_threshold
- Add custom linting rules
- Review all diffs manually

### Handling Large Codebases

- Scan once, then work incrementally
- Focus requests on specific modules
- Use clear module boundaries
- Keep tasks small and focused

### Debugging Issues

- Check logs: `docker-compose logs -f`
- Review state: `cat /state/workflow_state.json`
- Test manually: Open shell and run commands
- Start fresh: `make clean && make build`

## Getting the Most Out of AI Coding

### Set Clear Boundaries

The AI works best when:
- Requirements are explicit
- Scope is limited
- Success is measurable

### Iterative Refinement

Don't expect perfection first try:
1. Start with basic implementation
2. Add edge cases
3. Improve error handling
4. Refine and optimize

### Learn from Failures

When tasks fail:
- Review what went wrong
- Adjust your request
- Improve specifications
- Update tests

### Trust but Verify

Always:
- Read generated code
- Run tests manually
- Check edge cases
- Verify behavior

## Conclusion

The Local AI Coding Buddy is a tool to assist, not replace, human developers. Use it for routine tasks, let it handle boilerplate, but always apply human judgment to important decisions.

For more help:
- See TROUBLESHOOTING.md for issues
- See ARCHITECTURE.md for system details
- See examples/ for sample projects
