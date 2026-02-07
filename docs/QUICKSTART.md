# Quickstart Guide

Get up and running with Local AI Coding Buddy in 10 minutes.

## Prerequisites Check

```bash
# Check Docker
docker --version
# Should show: Docker version 20.10+ or higher

# Check docker-compose
docker-compose --version
# Should show: docker-compose version 1.29+ or higher

# Check available disk space
df -h .
# Need at least 20GB free
```

## Step-by-Step Setup

### 1. Download and Extract

```bash
# Extract the archive
cd local-coding-buddy

# Verify contents
ls -la
# Should see: docker-compose.yml, orchestrator/, agents/, config/, etc.
```

### 2. Run Setup

```bash
./scripts/setup.sh
```

This will:
- Verify Docker installation
- Create configuration files
- Build container images (~5-10 minutes)

### 3. Download Model

Choose one of these models:

**Option A: CodeLlama 7B (Recommended for coding)**
```bash
cd models
wget https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf
mv codellama-7b.Q4_K_M.gguf base-model.gguf
cd ..
```

**Option B: Mistral 7B (Better general reasoning)**
```bash
cd models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
mv mistral-7b-instruct-v0.2.Q4_K_M.gguf base-model.gguf
cd ..
```

### 4. Configure Your Project

```bash
# Copy example config
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
vim .env

# Set PROJECT_PATH to your project directory
# Example: PROJECT_PATH=/home/user/my-python-project
```

### 5. Start the System

```bash
# Start containers in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Wait for "Model loaded successfully" in the agent-runtime logs.

### 6. Test with Example

Let's try a simple task on a test project:

```bash
# Create test project
mkdir -p /tmp/test-project
cd /tmp/test-project
git init
touch README.md
git add . && git commit -m "Initial commit"

# Update .env to point to test project
# PROJECT_PATH=/tmp/test-project

# Run a simple task
docker-compose exec orchestrator python -m orchestrator.main run \
  --project /workspace \
  --request "Create a Python module with a function that adds two numbers and includes unit tests"
```

### 7. Review Results

```bash
# Check what was created
ls /tmp/test-project

# View the implementation
cat /tmp/test-project/*.py

# Check git history
cd /tmp/test-project
git log --oneline
```

## Common First-Time Issues

### "Model not found"
```bash
# Check model exists and is named correctly
ls -lh models/base-model.gguf

# If missing, download a model (see step 3)
```

### "Permission denied"
```bash
# Fix: Set correct user ID in .env
echo "CONTAINER_USER_ID=$(id -u)" >> .env
echo "CONTAINER_GROUP_ID=$(id -g)" >> .env

# Restart
docker-compose down
docker-compose up -d
```

### "Out of memory"
```bash
# Check Docker memory limit
docker stats

# Increase in Docker Desktop settings, or:
# Use smaller model quantization (Q2, Q3 instead of Q4)
```

### Container won't start
```bash
# View detailed logs
docker-compose logs orchestrator
docker-compose logs agent-runtime

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Next Steps

Once the basic setup works:

1. **Try a real project**: Point to your actual codebase
2. **Experiment with requests**: Test different coding tasks
3. **Adjust config**: Tune `config/config.yaml` for your needs
4. **Enable auto-commit**: Set `auto_commit: true` in config (once confident)
5. **Monitor performance**: Review logs and metrics

## Example Requests to Try

```bash
# Add new feature
--request "Add logging to all functions in module X"

# Refactor
--request "Extract validation logic into separate functions"

# Fix bugs
--request "Fix the edge case in function Y when input is empty"

# Add tests
--request "Add comprehensive unit tests for class Z"

# Documentation
--request "Add docstrings to all public functions"
```

## Getting Help

If stuck:
1. Check `README.md` for detailed documentation
2. Review `docker-compose logs` for errors
3. Verify your model file is valid (3-7GB for 7B models)
4. Ensure project path is correct in `.env`
5. Try with a simple test project first

## Stopping the System

```bash
# Stop containers but keep data
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Remove everything including models
docker-compose down -v
```

## Summary Checklist

- [ ] Docker and docker-compose installed
- [ ] Setup script completed successfully
- [ ] Model downloaded to `models/base-model.gguf`
- [ ] `.env` file configured with project path
- [ ] Containers started with `docker-compose up -d`
- [ ] Model loaded (check logs)
- [ ] Test task completed successfully

You're ready to code with your AI buddy! 🚀
