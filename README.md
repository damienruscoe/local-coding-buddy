# Local AI Coding Buddy

A fully autonomous local AI coding assistant built from small models, deterministic tooling, and strict orchestration.

## Overview

This system acts as a local "coding buddy" for C++ and Python projects, supporting both greenfield development and iterative work on existing codebases while preserving full developer control and visibility.

## Architecture

The system consists of three layers:

1. **Host Layer** — Developer-owned project workspace
2. **Infrastructure Layer** — Orchestration, tooling, execution (containerized)
3. **Agent Layer** — LLM-based reasoning components (containerized)

### Key Components

- **Orchestrator**: Python-based workflow engine with deterministic state machine
- **Agent Runtime**: FastAPI service hosting LLM inference via llama.cpp
- **Tool Executors**: Sandboxed test runners and build systems
- **Codebase Scanner**: Non-LLM static analysis for existing projects
- **Git Interface**: Version control integration with automatic rollback

### Agent Types

1. **Architect** - Decomposes requests into tasks
2. **Spec Author** - Generates tests from acceptance criteria
3. **Implementer** - Writes code to pass tests
4. **Reviewer** - Analyzes failures and suggests fixes
5. **Refiner** - Improves code structure (optional)

## Prerequisites

- Docker and docker-compose
- 8GB+ RAM (for model inference)
- 20GB+ disk space
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd local-coding-buddy
./scripts/setup.sh
```

### 2. Download a Model

Download a GGUF model and place it in `models/base-model.gguf`:

**Recommended models:**
- [CodeLlama-7B-GGUF](https://huggingface.co/TheBloke/CodeLlama-7B-GGUF)
- [Mistral-7B-Instruct-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)

```bash
# Example download (CodeLlama 7B, Q4 quantization)
wget https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf \
  -O models/base-model.gguf
```

### 3. Configure Your Project

Edit `.env`:

```bash
cp .env.example .env
# Edit PROJECT_PATH to point to your project
```

### 4. Start the System

```bash
docker-compose up -d
```

### 5. Run a Task

```bash
# Run a coding request
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Add a function to calculate Fibonacci numbers with tests"

# Check status
docker-compose exec orchestrator python -m orchestrator.main status

# Scan existing codebase
docker-compose exec orchestrator python -m orchestrator.main scan \
  --project /workspace
```

## Workflow

The system follows this workflow for each request:

```
USER REQUEST
 ↓
ARCHITECT (creates task graph)
 ↓
SPEC AUTHOR (generates tests)
 ↓
FOR EACH TASK:
   ↓
IMPLEMENTER (writes code)
   ↓
BUILD + TEST
   ├─ FAIL → REVIEWER → IMPLEMENTER (retry)
   ├─ FAIL LIMIT → REVERT
   ↓
REFINER (optional cleanup)
   ↓
FINAL BUILD + TEST
   ↓
GIT COMMIT (if auto-commit enabled)
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
max_retries: 3              # Max retry attempts per task
enable_refining: false      # Enable refactoring stage
coverage_threshold: 80.0    # Minimum test coverage %
agent_timeout: 300          # Agent call timeout (seconds)
test_timeout: 300          # Test execution timeout
auto_commit: false         # Auto-commit successful changes
```

## Project Structure

```
local-coding-buddy/
├── orchestrator/          # Workflow orchestration
│   ├── main.py           # CLI entry point
│   ├── state_machine.py  # State management
│   ├── scanner.py        # Codebase analyzer
│   ├── agents_client.py  # Agent communication
│   ├── validators.py     # Test runners & quality gates
│   └── git_interface.py  # Version control
├── agents/               # LLM runtime
│   ├── runtime.py        # FastAPI server
│   ├── model_loader.py   # llama.cpp wrapper
│   └── agent_prompts.py  # System prompts
├── config/              # Configuration files
├── scripts/             # Setup and utilities
├── docker-compose.yml   # Container orchestration
└── README.md           # This file
```

## Supported Languages & Frameworks

### Languages
- Python 3.8+
- C++11+

### Test Frameworks
- Python: pytest, unittest
- C++: googletest, CTest

## Limitations

By design, this system:
- Does NOT perform autonomous long-term planning
- Does NOT self-modify infrastructure code
- Does NOT redesign large system architectures
- Operates only on local code (no network by default)

These are intentional constraints for safety and predictability.

## Troubleshooting

### Model won't load
- Check that `models/base-model.gguf` exists
- Verify file size (should be 3-7GB for 7B models)
- Check container logs: `docker-compose logs agent-runtime`

### Tests failing
- Ensure project has proper test structure
- Check test framework is installed in container
- Review logs: `docker-compose logs orchestrator`

### Out of memory
- Reduce model size (use smaller quantization)
- Reduce `context_size` in config
- Increase Docker memory limit

### Permission errors
- Check `CONTAINER_USER_ID` and `CONTAINER_GROUP_ID` in `.env`
- Ensure they match your host user ID: `id -u` and `id -g`

## Development

### Running Tests

```bash
# Orchestrator tests
docker-compose exec orchestrator pytest /app/orchestrator/tests/

# Agent runtime tests
docker-compose exec agent-runtime pytest /app/agents/tests/
```

### Viewing Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
docker-compose logs -f agent-runtime
```

### Rebuilding

```bash
# Rebuild after code changes
docker-compose build

# Force rebuild without cache
docker-compose build --no-cache
```

## Security

The system includes several security measures:

- Containers run as non-root user
- No outbound network by default
- Resource limits (CPU/memory)
- Sandboxed execution
- Explicit file access allowlists

## Performance Tips

1. **Use quantized models**: Q4 or Q5 quantization balances quality and speed
2. **Adjust context size**: Smaller contexts = faster inference
3. **Enable refining selectively**: Adds overhead but improves code quality
4. **Set appropriate timeouts**: Balance patience vs. responsiveness

## Observability

The system logs to:
- `/state/orchestrator.log` (workflow events)
- Docker logs (container output)
- `/state/workflow_state.json` (current state)

Metrics tracked:
- Task success rate
- Retry count per task
- Test execution time
- Coverage percentage

## Contributing

This is an implementation of the design specified in:
- `local_coding_buddy_full_autonomous_system_architecture_infrastructure_agents.md`
- `local_ai_coding_buddy_complete_agentic_workflow_specification.md`

When contributing:
1. Follow the architectural principles (LLMs propose, tools decide)
2. Keep infrastructure deterministic
3. Maintain separation of concerns
4. Add tests for new functionality

## License

[Your chosen license]

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Review existing documentation
- Check logs for error details

## Acknowledgments

This system is designed to be **boring, strict, observable, and reliable** — the traits required for local AI to be trusted in production environments.
