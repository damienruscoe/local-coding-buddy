# Deployment Checklist

Use this checklist to ensure proper setup and deployment.

## Pre-Installation

- [ ] Docker Engine 20.10+ installed
- [ ] docker-compose 1.29+ installed
- [ ] At least 8GB RAM available
- [ ] At least 20GB disk space free
- [ ] Git installed and configured
- [ ] User has proper permissions (can run docker commands)

## Installation Steps

- [ ] Project files extracted/cloned
- [ ] Ran `./scripts/setup.sh`
- [ ] Setup completed without errors
- [ ] `.env` file created and configured
- [ ] `PROJECT_PATH` set to correct directory
- [ ] User ID and Group ID configured (if needed)

## Model Setup

- [ ] Model downloaded (3-7GB GGUF file)
- [ ] Model placed at `models/base-model.gguf`
- [ ] Model file size verified (not corrupted)
- [ ] Model is compatible format (GGUF for llama.cpp)

## Container Build

- [ ] Ran `docker-compose build`
- [ ] Build completed successfully
- [ ] No errors in build logs
- [ ] Images created (check with `docker images`)

## First Run

- [ ] Ran `docker-compose up -d`
- [ ] All containers started (check with `docker-compose ps`)
- [ ] No error messages in logs
- [ ] Model loaded successfully (check agent-runtime logs)
- [ ] Health check passes: `curl http://localhost:8000/health`

## Configuration

- [ ] Reviewed `config/config.yaml`
- [ ] Adjusted settings for your needs
- [ ] Coverage threshold appropriate
- [ ] Timeouts suitable for your hardware
- [ ] Temperature set correctly (0.3-0.9)

## Test Project Setup

- [ ] Test project directory created
- [ ] Git initialized in test project
- [ ] Initial commit made
- [ ] Test project path configured in `.env`

## Verification Tests

- [ ] System status command works:
  ```bash
  docker-compose exec orchestrator python -m orchestrator.main status
  ```

- [ ] Scan command works:
  ```bash
  docker-compose exec orchestrator python -m orchestrator.main scan --project /workspace
  ```

- [ ] Simple test request completes:
  ```bash
  docker-compose exec orchestrator python -m orchestrator.main run \
    --project /workspace \
    --request "Add a hello world function with a test"
  ```

## Performance Checks

- [ ] Container memory usage acceptable (`docker stats`)
- [ ] Model inference works (< 60s for simple requests)
- [ ] Test execution works
- [ ] Git operations work

## Security Review

- [ ] Containers run as non-root user
- [ ] File permissions correct
- [ ] No sensitive data in configuration
- [ ] Network isolation configured
- [ ] Resource limits appropriate

## Documentation Review

- [ ] Read README.md
- [ ] Reviewed QUICKSTART.md
- [ ] Skimmed USER_GUIDE.md
- [ ] Know where TROUBLESHOOTING.md is
- [ ] Understand ARCHITECTURE.md basics

## Production Readiness (Optional)

If using in production:

- [ ] Auto-commit disabled initially
- [ ] Manual review process established
- [ ] Backup strategy for project files
- [ ] Monitoring configured
- [ ] Log retention policy set
- [ ] Regular cleanup scheduled

## Post-Deployment

- [ ] Bookmarked documentation
- [ ] Created initial project backup
- [ ] Tested rollback procedure
- [ ] Team trained on usage
- [ ] Documented custom configurations

## Maintenance Schedule

Set up regular maintenance:

- [ ] Weekly: `docker system prune`
- [ ] Monthly: Review and archive logs
- [ ] Quarterly: Update model if new versions available
- [ ] As needed: Update container images

## Common Issues Checklist

If problems occur, verify:

- [ ] Model file exists and is correct size
- [ ] Permissions are correct (user ID matches)
- [ ] Enough free disk space
- [ ] Enough free RAM (check `free -h`)
- [ ] Docker daemon running
- [ ] No port conflicts (8000)
- [ ] Project path is accessible

## Success Criteria

You're ready when:

- [ ] All containers healthy
- [ ] Simple test request succeeds
- [ ] Changes committed to git
- [ ] No error messages in logs
- [ ] Performance is acceptable
- [ ] Team can use basic features

## Emergency Procedures

Document these before issues occur:

1. **Stop everything**: `docker-compose down`
2. **Rollback project**: `cd project && git reset --hard HEAD`
3. **Reset state**: `rm /state/workflow_state.json`
4. **Restart fresh**: `docker-compose up -d`
5. **Get help**: Check TROUBLESHOOTING.md

## Notes

Space for deployment-specific notes:

```
Date deployed: _______________
Deployed by: _________________
Model used: __________________
Project path: ________________
Special config: ______________
Known issues: ________________
```

## Sign-Off

- [ ] Deployment complete and verified
- [ ] Documentation reviewed
- [ ] Team notified
- [ ] Ready for use

Deployed by: _________________ Date: _________________
