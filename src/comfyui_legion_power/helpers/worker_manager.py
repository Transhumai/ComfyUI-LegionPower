import os
import subprocess
import sys
import time
import urllib.request
import threading
import shlex

WORKER_PROCESSES = {}
WORKER_PORTS = {}
PORT_LOCK = threading.Lock()

from ..legion_config_manager import config_manager, COMFYUI_ROOT_PATH


class LegionWorkerManager:
    @staticmethod
    def _get_config_hash(config):
        port = config.get('comfyui.port')
        if port != 'auto':
            return f"port_{port}"

        # For 'auto' port, create hash based on config content
        # This ensures same config content = same worker, even if object is recreated
        import hashlib
        import json

        # Get relevant config keys that should trigger new worker
        relevant_keys = [
            'comfyui.type',
            'comfyui.paths.comfyui_path',
            'comfyui.paths.python_executable',
            'comfyui.paths.custom_nodes_template',
            'execution.extra_args',
            'execution.env_vars',
        ]

        config_dict = {key: config.get(key) for key in relevant_keys}
        config_str = json.dumps(config_dict, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]

        return f"auto_{config_hash}"


    @staticmethod
    def is_worker_alive(port):
        if not port: return False
        url = f"http://127.0.0.1:{port}/queue"
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                return response.status == 200
        except:
            return False

    @staticmethod
    def ensure_worker_is_alive(campaign):
        with PORT_LOCK:
            config = campaign.config
            config_hash = LegionWorkerManager._get_config_hash(config)

            if config_hash in WORKER_PORTS:
                port = WORKER_PORTS[config_hash]
                if LegionWorkerManager.is_worker_alive(port):
                    print(f"[LegionPower] Found existing worker for config on port {port}.")
                    campaign.resolved_port = port
                    return
                else:
                    print(f"[LegionPower] Found dead worker on port {port}. Will restart.")
                    if port in WORKER_PROCESSES: del WORKER_PROCESSES[port]

            port_config = config.get('comfyui.port')
            if port_config != 'auto':
                if LegionWorkerManager.is_worker_alive(port_config):
                    print(f"[LegionPower] Found externally-run worker on specified port {port_config}.")
                    campaign.resolved_port = port_config
                    WORKER_PORTS[config_hash] = port_config
                    return

            port_to_launch = LegionWorkerManager._get_next_available_port() if port_config == 'auto' else port_config

            print(f"[LegionPower] Launching new ComfyUI worker instance on port {port_to_launch}...")


            python_executable = config.get('comfyui.paths.python_executable')
            if not python_executable:
                python_executable = sys.executable # Use the same Python as the Master

            main_py_path = config.get('comfyui.paths.comfyui_path')
            if main_py_path:
                main_py_path = main_py_path / "main.py"
            else:
                main_py_path = COMFYUI_ROOT_PATH / "main.py"

            print(f"[LegionPower]  - Python executable: {python_executable}")
            print(f"[LegionPower]  - Main.py path: {main_py_path}")

            command = [
                python_executable,
                str(main_py_path),
                '--port', str(port_to_launch),
                '--disable-auto-launch',
                '--dont-print-server',
            ]

            # Handle extra_args
            extra_args = config.get("execution.extra_args")
            if extra_args:
                if isinstance(extra_args, str):
                    # Split string into args (respects quotes)
                    extra_args_list = shlex.split(extra_args)
                    command.extend(extra_args_list)
                    print(f"[LegionPower]  - Added extra args: {extra_args}")
                elif isinstance(extra_args, list):
                    command.extend(extra_args)
                    print(f"[LegionPower]  - Added extra args: {' '.join(extra_args)}")

            # Environment variables handling
            env = os.environ.copy() # Copy Master process environment

            # Apply custom environment variables from config
            custom_env_vars = config.get("execution.env_vars")
            if custom_env_vars and isinstance(custom_env_vars, dict):
                for key, value in custom_env_vars.items():
                    env[key] = str(value)
                    print(f"[LegionPower]  - Set env var: {key}={value}")

            print(f"[LegionPower]  - CWD: {COMFYUI_ROOT_PATH}")
            print(f"[LegionPower]  - Command: {' '.join(command)}")

            # Launch the process with correct CWD and environment
            process = subprocess.Popen(
                command,
                cwd=COMFYUI_ROOT_PATH,
                env=env
            )

            WORKER_PROCESSES[port_to_launch] = process
            WORKER_PORTS[config_hash] = port_to_launch
            campaign.resolved_port = port_to_launch

            print(f"[LegionPower] Worker process launched with PID: {process.pid}. Waiting for it to come online...")

            for _ in range(200):
                if LegionWorkerManager.is_worker_alive(port_to_launch):
                    print(f"[LegionPower] Worker on port {port_to_launch} is now online.")
                    return
                time.sleep(1.5)

            raise RuntimeError(f"Worker on port {port_to_launch} failed to start in time.")

    @staticmethod
    def _get_next_available_port():
        start_port = config_manager.get('ports.start_port')
        max_workers = config_manager.get('ports.max_workers')
        for i in range(max_workers):
            port = start_port + i
            if port not in WORKER_PROCESSES and not LegionWorkerManager.is_worker_alive(port):
                return port
        raise ConnectionError("No available ports found for new workers.")