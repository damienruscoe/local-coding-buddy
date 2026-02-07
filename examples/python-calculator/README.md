# Example Python Calculator

A simple calculator project to test the Local AI Coding Buddy.

## What's Here

- `calculator.py` - Basic arithmetic functions
- `test_calculator.py` - Unit tests

## Testing the Coding Buddy

Try these requests:

### 1. Add Multiplication
```bash
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add multiply and divide functions with comprehensive unit tests"
```

### 2. Add Input Validation
```bash
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add type checking and raise TypeError for non-numeric inputs"
```

### 3. Add Documentation
```bash
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add detailed docstrings to all functions with examples"
```

### 4. Add More Features
```bash
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add power, square root, and absolute value functions"
```

## Running Tests Manually

```bash
cd examples/python-calculator
python -m pytest test_calculator.py -v
```

## Expected Workflow

1. System scans the existing code
2. Architect creates task breakdown
3. Spec Author generates tests
4. Implementer writes code
5. Validator runs tests
6. On success, changes are committed

## What to Observe

- Task decomposition quality
- Test generation
- Code implementation
- Retry behavior on failures
- Git commits

This simple project is ideal for testing because:
- Small scope (fits in context)
- Clear requirements
- Easy to verify
- Fast test execution
