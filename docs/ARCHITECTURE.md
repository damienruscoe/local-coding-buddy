# System Architecture Overview

## Design Philosophy

This system follows three core principles:

1. **LLMs propose; tools decide**
   - Agents generate suggestions
   - Infrastructure validates and enforces rules
   - No agent judges its own output

2. **Reasoning is expensive; constraints are cheap**
   - Use deterministic code wherever possible
   - Invoke LLMs only for tasks requiring reasoning
   - Enforce limits through infrastructure, not prompts

3. **State lives outside models**
   - No conversational memory in agents
   - Explicit state persistence in JSON/files
   - Every step is reproducible

## System Layers

### 1. Host Layer

**Location**: Your machine  
**Ownership**: Developer  
**Contents**: 
- Project source code
- Git repository
- Build artifacts
- Test files

**Characteristics**:
- Not containerized
- Full developer control
- Persistent across runs

### 2. Infrastructure Layer

**Location**: Docker containers  
**Language**: Python  
**Components**:

#### Orchestrator
- State machine implementation
- Workflow coordination
- Rule enforcement
- Git integration
- Tool execution

#### Scanner
- Static code analysis
- Dependency extraction
- Symbol indexing
- No LLM usage

#### Validators
- Test execution (pytest, CTest)
- Coverage measurement
- Linting (pylint, black, clang-tidy)
- Quality gate enforcement

#### Git Interface
- Branch management
- Commit/rollback
- Diff generation

**Characteristics**:
- Deterministic
- Stateless (state persisted to disk)
- No LLM reasoning

### 3. Agent Layer

**Location**: Docker container  
**Language**: Python + llama.cpp  
**Components**:

#### Model Runtime
- FastAPI service
- llama.cpp wrapper
- Single shared model
- Role-based prompting

#### Agent Types
- **Architect**: Task decomposition
- **Spec Author**: Test generation
- **Implementer**: Code writing
- **Reviewer**: Failure analysis
- **Refiner**: Code improvement

**Characteristics**:
- Stateless (context provided per call)
- Sandboxed
- Resource-limited
- Role determined by system prompt

## Data Flow

```
┌─────────────┐
│ User Request│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Orchestrator   │◄────── State File
│ (State Machine) │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Scanner│────► Codebase Summary
    └────────┘
         │
         ▼
    ┌──────────┐
    │Architect │────► Task Graph (JSON)
    │  Agent   │
    └──────────┘
         │
         ▼
    ┌───────────┐
    │Spec Author│────► Test Files
    │   Agent   │
    └───────────┘
         │
         ▼
    ┌─────────────┐
    │ Implementer │────► Code Diff
    │    Agent    │
    └─────────────┘
         │
         ▼
    ┌───────────┐
    │ Validator │────► Pass/Fail + Metrics
    └───────────┘
         │
         ├─ Fail ─► ┌──────────┐
         │          │ Reviewer │──► Suggestions
         │          │  Agent   │
         │          └──────────┘
         │               │
         │               └─► Retry (up to max)
         │
         ▼ Pass
    ┌─────────┐
    │ Refiner │────► Improved Diff
    │  Agent  │      (optional)
    └─────────┘
         │
         ▼
    ┌────────────────┐
    │Final Validation│
    └───────┬────────┘
            │
            ▼ Pass
    ┌─────────────┐
    │ Git Commit  │
    └─────────────┘
```

## State Machine

```
States:
- IDLE: Waiting for request
- SCANNING_CODEBASE: Analyzing existing code
- PLANNING: Decomposing into tasks
- TEST_AUTHORING: Generating tests
- IMPLEMENTING: Writing code
- VALIDATING: Running tests
- REVIEW: Analyzing failures
- REFINING: Improving code
- FINAL_VALIDATION: Last check
- COMMIT: Persisting changes
- DONE: Success
- FAILED: Error state
- ROLLBACK: Reverting changes

Transitions:
IDLE → SCANNING_CODEBASE → PLANNING → TEST_AUTHORING → IMPLEMENTING
                                                            ↓
FINAL_VALIDATION ← REFINING ← VALIDATING (pass) ←──────────┘
       │                           │
       │                           │ (fail, retries remain)
       │                           ↓
       │                        REVIEW → IMPLEMENTING
       │                           │
       │                           │ (fail, no retries)
       │                           ↓
       │                        ROLLBACK → FAILED
       │
       │ (pass)
       ↓
    COMMIT → DONE
```

## Security Model

### Container Isolation
- No network access by default
- Non-root user (UID 1000)
- Dropped capabilities
- Resource limits (CPU, memory)

### File System
- Read/write: Project directory only
- Read-only: Infrastructure code
- No access to host system

### Execution Sandboxing
- Timeouts on all subprocess calls
- Resource quotas
- Explicit allow-lists

## Model Strategy

### Single Foundation Model
- One base model (7B-13B parameters)
- GGUF format for llama.cpp
- Quantized (Q4/Q5) for efficiency

### Role Specialization
Agents share the same model but differ in:
- System prompts
- Temperature settings
- Max token limits
- Context windows

**Why?**
- Reduces disk usage (no duplication)
- Simplifies model management
- Proven effective in practice

### Optional Extensions
- Code-tuned model for Implementer
- LoRA adapters for specialization

## Codebase Handling

### Greenfield Projects
- Full context available
- Sequential task execution

### Existing Codebases
Progressive disclosure strategy:

1. **Scan Phase**
   - Extract file tree
   - Build dependency graph
   - Index symbols
   - Generate summaries

2. **Planning Phase**
   - Architect receives summaries, not source
   - Works with abstractions

3. **Implementation Phase**
   - Implementer receives:
     - One file at a time
     - Immediate dependencies only
     - Relevant context snippets

**Benefit**: Scales to large codebases without exceeding context limits

## Quality Enforcement

### Test-First Approach
1. Generate tests before implementation
2. Tests define correctness
3. Implementation must pass tests
4. Tests cannot be modified after approval

### Coverage Requirements
- Minimum threshold (default: 80%)
- Per-file tracking
- Regression prevention

### Static Analysis
- Python: pylint, black
- C++: clang-tidy, cppcheck
- Custom rules via configuration

### Automatic Rollback
Triggered by:
- Test failures after max retries
- Coverage regression
- Critical linting errors
- Build failures

## Observability

### Logs
- Structured JSON logs
- Per-component streams
- Persisted to volume

### Metrics
- Task success rate
- Retry count distribution
- Test execution time
- Coverage trends
- Agent call duration

### State Inspection
```bash
# Current state
docker-compose exec orchestrator python -m orchestrator.main status

# Full state file
cat state/workflow_state.json

# Logs
tail -f state/orchestrator.log
```

## Extension Points

### Adding New Languages
1. Add file extensions to scanner
2. Add test framework support to validators
3. Update agent prompts

### Custom Quality Gates
1. Add validator functions
2. Update configuration schema
3. Integrate into validation pipeline

### Additional Agents
1. Define system prompt
2. Add to `agent_prompts.py`
3. Create client method in `agents_client.py`
4. Update orchestrator workflow

## Performance Characteristics

### Typical Request Flow
- Scan: 5-30 seconds
- Planning: 10-60 seconds
- Test generation: 15-45 seconds
- Implementation: 30-120 seconds per task
- Validation: 10-300 seconds

**Total**: 2-10 minutes for simple requests

### Resource Usage
- Orchestrator: ~100MB RAM
- Agent runtime: 4-8GB RAM (model-dependent)
- Disk: 5-10GB (model + containers)

### Optimization Options
1. Use smaller quantization (Q2/Q3)
2. Reduce context size
3. Disable refining stage
4. Parallel task execution (future)

## Failure Modes

### Agent Failures
- Timeout → Retry with same prompt
- Invalid JSON → Parse correction → Retry
- Max retries → Rollback

### Infrastructure Failures
- Build failure → Stop, report error
- Test timeout → Mark as failed
- Git operation failure → Manual intervention

### Recovery
All failures leave system in clean state:
- Changes rolled back via Git
- State file updated
- Logs preserved for debugging

## Future Enhancements

Possible improvements (not implemented):
1. Parallel task execution
2. Incremental compilation
3. Caching agent responses
4. Multi-model support
5. Web UI dashboard
6. Plugin system
7. Cloud model fallback

## Summary

This architecture prioritizes:
- **Reliability**: Deterministic infrastructure, explicit state
- **Observability**: Comprehensive logging and metrics
- **Safety**: Sandboxing, rollback, quality gates
- **Simplicity**: Boring technology, clear boundaries
- **Efficiency**: Single model, minimal context

The result is a system that is **boring, strict, observable, and reliable** — exactly what's needed for trustworthy local AI assistance.
