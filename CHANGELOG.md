# Changelog

All notable changes to the Local AI Coding Buddy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-07

### Initial Release

#### Added
- Core orchestrator with state machine implementation
- Agent runtime with llama.cpp integration
- Five specialized agents: Architect, Spec Author, Implementer, Reviewer, Refiner
- Codebase scanner for existing projects
- Test runners for Python (pytest) and C++ (googletest/CTest)
- Quality gates: coverage checking, linting, formatting
- Git integration with automatic rollback
- Docker containerization with security isolation
- Configuration system via YAML
- Comprehensive documentation:
  - README.md
  - QUICKSTART.md
  - USER_GUIDE.md
  - ARCHITECTURE.md
  - TROUBLESHOOTING.md
  - DEPLOYMENT_CHECKLIST.md
- Example Python calculator project
- Setup and deployment scripts
- Makefile for common operations

#### Features
- **Multi-language support**: Python and C++
- **Test-first development**: Tests generated before implementation
- **Automatic validation**: Tests run automatically with coverage tracking
- **Retry logic**: Up to 3 retries on failure with agent review
- **Rollback protection**: Automatic git rollback on persistent failures
- **Progressive disclosure**: Smart context management for large codebases
- **Sandboxed execution**: Isolated containers with resource limits
- **Deterministic infrastructure**: Non-LLM code for reliability
- **Single model architecture**: One base model for all agents
- **State persistence**: All state saved to disk, no in-memory dependencies

#### Security
- Containers run as non-root user (UID 1000)
- No network access by default
- Dropped Linux capabilities
- Resource limits (CPU/memory)
- File access restricted to project directory

#### Documentation
- Complete architecture documentation
- Step-by-step quickstart guide
- Comprehensive user guide with examples
- Troubleshooting guide for common issues
- Deployment checklist for production use

### Known Limitations

This initial release has the following limitations:

- **Single project at a time**: Can only work on one project per deployment
- **CPU-only inference**: GPU support requires manual configuration
- **Basic CMake detection**: Complex build systems may need manual setup
- **Sequential task execution**: No parallel processing of tasks
- **Limited language support**: Only Python and C++ currently
- **No web UI**: Command-line interface only
- **Local models only**: No cloud model integration

### Requirements

- Docker Engine 20.10+
- docker-compose 1.29+
- 8GB+ RAM
- 20GB+ disk space
- Git
- GGUF-format model (7B-13B parameters recommended)

### Tested Configurations

- **OS**: Ubuntu 22.04, macOS 13+, Windows 11 (WSL2)
- **Docker**: 20.10.x - 24.x
- **Models**: CodeLlama-7B, Mistral-7B, Llama2-7B
- **Python versions**: 3.8 - 3.11
- **C++ standards**: C++11, C++14, C++17

### Migration Guide

This is the initial release - no migration needed.

### Contributors

- Initial implementation based on design specifications

## [Unreleased]

### Planned Features

Future enhancements being considered:

- [ ] GPU support (CUDA/ROCm)
- [ ] Additional language support (JavaScript, Rust, Go)
- [ ] Web UI dashboard
- [ ] Parallel task execution
- [ ] Cloud model fallback option
- [ ] Plugin system for extensibility
- [ ] Enhanced codebase scanner with tree-sitter
- [ ] Incremental compilation support
- [ ] Agent response caching
- [ ] Multi-project workspace support
- [ ] IDE integrations (VSCode, JetBrains)
- [ ] Metrics dashboard and visualization
- [ ] Custom test framework support
- [ ] Advanced refactoring patterns
- [ ] Conversation-based task refinement

### Under Consideration

- Support for additional test frameworks
- Integration with CI/CD platforms
- Collaborative multi-agent workflows
- Fine-tuned models for specific domains
- Telemetry and analytics (opt-in)

---

## Version History

- **0.1.0** (2024-02-07) - Initial release

## How to Contribute

See CONTRIBUTING.md for guidelines on proposing changes and submitting pull requests.

## Support

For issues and questions:
- Review documentation in `docs/`
- Check TROUBLESHOOTING.md for common problems
- Search existing issues
- Open a new issue with detailed information

## License

This project is licensed under the MIT License - see LICENSE file for details.
