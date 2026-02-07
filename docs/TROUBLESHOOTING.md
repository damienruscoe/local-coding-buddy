# Troubleshooting Guide

## Quick Diagnostics

Run these commands to check system health:

```bash
# Check container status
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Check model is loaded
docker-compose logs agent-runtime | grep "Model loaded"

# Verify state
docker-compose exec orchestrator python -m orchestrator.main status
```

## Common Issues

### 1. "Model not found" Error

**Symptoms**:
- Agent runtime fails to start
- Logs show: `FileNotFoundError: models/base-model.gguf`

**Solutions**:

```bash
# Check if model exists
ls -lh models/base-model.gguf

# If missing, download a model
cd models
wget https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf
mv codellama-7b.Q4_K_M.gguf base-model.gguf
cd ..

# Restart services
docker-compose restart agent-runtime
```

### 2. "Permission denied" Errors

**Symptoms**:
- Cannot write to project directory
- Git operations fail
- Log shows: `PermissionError`

**Solutions**:

```bash
# Check current user ID
id -u
id -g

# Update .env with your user ID
echo "CONTAINER_USER_ID=$(id -u)" >> .env
echo "CONTAINER_GROUP_ID=$(id -g)" >> .env

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### 3. Out of Memory

**Symptoms**:
- Container killed unexpectedly
- System becomes unresponsive
- Docker logs show: `OOMKilled`

**Solutions**:

**Option A: Use smaller model**
```bash
# Download smaller quantization (Q2 or Q3)
cd models
wget https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q2_K.gguf
mv codellama-7b.Q2_K.gguf base-model.gguf
cd ..
```

**Option B: Increase Docker memory**
- Docker Desktop: Settings → Resources → Memory (set to 8GB+)
- Linux: Edit `/etc/docker/daemon.json`

**Option C: Reduce context size**
```yaml
# In config/config.yaml
context_size: 2048  # Reduce from 4096
```

### 4. Agent Timeout

**Symptoms**:
- Tasks fail with timeout error
- Logs show: `Agent call timed out after 300 seconds`

**Solutions**:

```yaml
# In config/config.yaml
agent_timeout: 600  # Increase timeout (in seconds)
```

Or use faster model/quantization.

### 5. Tests Fail to Run

**Symptoms**:
- Validation step fails
- "Test framework not found"

**Solutions**:

**For Python projects**:
```bash
# Verify pytest is available
docker-compose exec orchestrator pytest --version

# If missing, add to project
cd your-project
pip install pytest
```

**For C++ projects**:
```bash
# Verify googletest
docker-compose exec orchestrator ls /usr/include/gtest

# Check CMakeLists.txt has test configuration
```

### 6. Build Failures (C++)

**Symptoms**:
- CMake configuration fails
- Compilation errors

**Solutions**:

```bash
# Check CMakeLists.txt exists
ls your-project/CMakeLists.txt

# Verify build directory
docker-compose exec orchestrator ls /workspace/build

# Manual build test
docker-compose exec orchestrator bash
cd /workspace
mkdir -p build && cd build
cmake ..
cmake --build .
```

### 7. Git Issues

**Symptoms**:
- "Not a git repository"
- Cannot commit

**Solutions**:

```bash
# Initialize git if needed
cd your-project
git init
git add .
git commit -m "Initial commit"

# Verify git config
git config user.name "Your Name"
git config user.email "your@email.com"
```

### 8. Agent Returns Invalid JSON

**Symptoms**:
- Planning fails with JSON parse error
- Logs show: `JSONDecodeError`

**Solutions**:

This usually indicates:
- Model is too small/weak
- Temperature too high
- Prompt issues

```yaml
# In config/config.yaml
temperature: 0.5  # Reduce from 0.7 for more deterministic output
```

Or try a different model (Mistral often better at JSON).

### 9. Coverage Below Threshold

**Symptoms**:
- Tests pass but validation fails
- "Coverage 65% below threshold 80%"

**Solutions**:

**Option A: Adjust threshold**
```yaml
# In config/config.yaml
coverage_threshold: 60.0  # Lower threshold
```

**Option B: Request better coverage**
```bash
# In your request, explicitly ask for comprehensive tests
--request "Add feature X with comprehensive unit tests achieving >80% coverage"
```

### 10. Network Issues

**Symptoms**:
- Cannot download models
- Setup script fails

**Solutions**:

```bash
# If behind proxy, configure Docker
# ~/.docker/config.json
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.example.com:8080",
      "httpsProxy": "http://proxy.example.com:8080"
    }
  }
}

# Restart Docker daemon
sudo systemctl restart docker
```

## Advanced Debugging

### View State File

```bash
# Current workflow state
docker-compose exec orchestrator cat /state/workflow_state.json | jq .
```

### Interactive Shell

```bash
# Orchestrator
docker-compose exec orchestrator bash

# Agent runtime
docker-compose exec agent-runtime bash
```

### Manual Agent Test

```bash
# Test agent directly
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "implementer",
    "prompt": "Write a hello world function",
    "max_tokens": 500
  }'
```

### Check Resource Usage

```bash
# Real-time stats
docker stats

# Detailed container info
docker-compose exec orchestrator ps aux
docker-compose exec orchestrator free -h
```

### Verbose Logging

```bash
# Enable debug logging
# In config/config.yaml
log_level: DEBUG

# Restart to apply
docker-compose restart orchestrator
```

## Performance Issues

### Slow Task Execution

**Check**:
1. Model size/quantization
2. CPU vs GPU usage
3. Context size
4. Concurrent container resource usage

**Optimize**:
```yaml
# config/config.yaml
context_size: 2048      # Smaller context
max_tokens: 1024        # Fewer tokens generated
```

### Disk Space Issues

```bash
# Check Docker disk usage
docker system df

# Clean up old containers/images
docker system prune -a

# Check model size
du -h models/
```

## Recovery Procedures

### Reset Everything

```bash
# Nuclear option: complete reset
docker-compose down -v
rm -rf models/*
rm .env
./scripts/setup.sh
# Re-download model
```

### Rollback Stuck Task

```bash
# Force rollback
docker-compose exec orchestrator python -c "
from orchestrator.git_interface import GitInterface
from pathlib import Path
git = GitInterface(Path('/workspace'))
git.rollback()
"
```

### Clear State

```bash
# Remove state file to start fresh
docker-compose exec orchestrator rm /state/workflow_state.json

# Restart
docker-compose restart orchestrator
```

## Getting Help

If none of these solutions work:

1. **Collect diagnostic info**:
   ```bash
   docker-compose logs > debug.log
   docker-compose exec orchestrator cat /state/orchestrator.log >> debug.log
   docker-compose ps >> debug.log
   docker system df >> debug.log
   ```

2. **Check the logs** for specific error messages

3. **Verify prerequisites**:
   - Docker version 20.10+
   - docker-compose 1.29+
   - 8GB+ RAM available
   - 20GB+ disk space

4. **Try with a minimal test project** to isolate the issue

5. **Review configuration** in `config/config.yaml` and `.env`

## Known Limitations

1. **Large codebases**: Scanner may be slow on 10,000+ files
   - Workaround: Scan only relevant subdirectories

2. **Complex build systems**: CMake detection is basic
   - Workaround: Manually configure build steps

3. **Network-dependent tests**: Will fail in isolated containers
   - Workaround: Mock network calls in tests

4. **GPU support**: Requires CUDA/ROCm setup
   - Current version is CPU-only by default

5. **Windows paths**: May have issues with path separators
   - Workaround: Use WSL2

## Preventive Measures

To avoid issues:

1. **Start small**: Test with simple projects first
2. **Version control**: Always have git commits before running
3. **Monitor resources**: Keep an eye on `docker stats`
4. **Regular cleanup**: Run `docker system prune` weekly
5. **Backup models**: Keep model files backed up
6. **Document changes**: Track what requests work well

## Still Stuck?

Create an issue with:
- Output of diagnostic commands above
- Your `docker-compose.yml` and `config/config.yaml`
- Relevant log excerpts
- Steps to reproduce

The more information you provide, the easier it is to help!
