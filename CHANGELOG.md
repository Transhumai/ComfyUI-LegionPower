# Changelog

All notable changes to ComfyUI-LegionPower will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-30

### Added
- Initial MVP release
- Core workflow orchestration system
- Legion: Configuration node for worker settings
- Legion: Master node (3/6/12 channel variants) for workflow execution
- Legion: Importer node for receiving data in worker
- Legion: Exporter node for sending results from worker  
- Legion: Join Campaign node for async result retrieval
- Legion: Join All Campaigns node for multi-workflow synchronization
- Legion: Warmupper node for pre-starting workers
- Serialization system for images (single and batch) and primitives
- Automatic worker lifecycle management
- Multi-GPU support via port-based worker isolation
- Sync and async execution modes
- Automatic workflow patching
- `extra_args` support for custom ComfyUI command-line arguments
- `env_vars` support for custom environment variables (GPU selection, memory config, etc.)
- Comprehensive documentation and examples

### Technical Details
- HTTP-based worker communication
- History-based execution completion detection
- Automatic port assignment
- Worker process reuse for identical configurations
- Temporary file-based data exchange with automatic cleanup
- JSON manifest-based serialization protocol

### Known Limitations
- Polling-based execution monitoring (WebSocket planned for v0.2)
- Limited serializer support (images and primitives only)
- Local workers only (Docker/remote support planned)
- Windows and Linux support (macOS untested)

---

## [Unreleased]

### Planned for v0.2
- WebSocket-based execution monitoring
- LATENT, CONDITIONING, MODEL serializers
- Docker worker support
- Remote worker support (RunPod, Vast.ai)
- Worker pool with priority queue
- GPU affinity configuration
- Improved error handling and reporting

---

[0.1.0]: https://github.com/Transhumai/ComfyUI-LegionPower/releases/tag/v0.1.0
