# LegionPower Quick Reference

## Environment Variables Guide

### GPU Selection

```yaml
# Use specific GPU
env_vars:
  CUDA_VISIBLE_DEVICES: "1"

# Use multiple GPUs
env_vars:
  CUDA_VISIBLE_DEVICES: "0,1"

# CPU only
env_vars:
  CUDA_VISIBLE_DEVICES: ""
```

### Memory Management

```yaml
# Reduce memory fragmentation
env_vars:
  PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"

# More aggressive (for very limited VRAM)
env_vars:
  PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:256,garbage_collection_threshold:0.6"
```

### Compilation & Performance

```yaml
# Disable torch compilation
env_vars:
  TORCH_COMPILE_DISABLE: "1"

# Enable synchronous CUDA (debugging)
env_vars:
  CUDA_LAUNCH_BLOCKING: "1"
```

### Common Combinations

#### Low VRAM Setup (8GB GPU)
```yaml
execution:
  extra_args: "--lowvram"
  env_vars:
    CUDA_VISIBLE_DEVICES: "0"
    PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:256"
```

#### Multi-GPU Production
```yaml
execution:
  env_vars:
    CUDA_VISIBLE_DEVICES: "1,2"
    PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:1024"
```

#### Debugging Setup
```yaml
execution:
  extra_args: "--verbose"
  env_vars:
    CUDA_LAUNCH_BLOCKING: "1"
    TORCH_DISTRIBUTED_DEBUG: "DETAIL"
```

## Command-Line Arguments (extra_args)

```yaml
# Common args
extra_args: "--lowvram"              # Low VRAM mode
extra_args: "--highvram"             # High VRAM mode
extra_args: "--normalvram"           # Normal VRAM mode
extra_args: "--gpu-only"             # GPU only processing
extra_args: "--preview-method auto"  # Auto preview method

# Multiple args
extra_args: "--lowvram --preview-method auto --verbose"

# Or as list
extra_args: 
  - "--lowvram"
  - "--preview-method"
  - "auto"
```

## Port Configuration

```yaml
# Automatic port (8200, 8201, 8202...)
comfyui:
  port: auto

# Fixed port
comfyui:
  port: 8200

# Use externally-running ComfyUI
comfyui:
  port: 8188  # If you manually started ComfyUI on 8188
```

## Execution Modes

```yaml
# Synchronous (blocking)
execution:
  asynch: false
  # Master node waits for completion, returns results immediately

# Asynchronous (non-blocking)
execution:
  asynch: true
  # Master node returns immediately, use LegionJoin to get results
```

## Complete Example

```yaml
comfyui:
  type: local_process
  port: auto

execution:
  dry_run: false
  asynch: false
  
  extra_args: "--lowvram --preview-method auto"
  
  env_vars:
    CUDA_VISIBLE_DEVICES: "1"
    PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"
    TORCH_COMPILE_DISABLE: "1"

workflow: my_workflow.json
```

## Troubleshooting

### Worker won't start
- Check port isn't in use: `netstat -an | grep 8200`
- Check CUDA_VISIBLE_DEVICES points to valid GPU
- Check ComfyUI path is correct

### Out of memory
- Add `--lowvram` to extra_args
- Reduce `max_split_size_mb` to 256 or 128
- Use CPU-only mode: `CUDA_VISIBLE_DEVICES: ""`

### Worker uses wrong GPU
- Set `CUDA_VISIBLE_DEVICES` explicitly
- Verify with `nvidia-smi` which GPU is being used

### Slow execution
- Remove `CUDA_LAUNCH_BLOCKING: "1"` (debugging only)
- Try `--normalvram` or `--highvram`
- Check you're not using CPU-only mode accidentally

## Links

- Full docs: [README.md](README.md)
- Examples: [examples/](examples/)
- Issues: https://github.com/Transhumai/ComfyUI-LegionPower/issues
