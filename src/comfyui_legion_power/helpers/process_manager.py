# src/comfyui_legion_power/helpers/process_manager.py

import subprocess
import sys
from pathlib import Path
import time
import urllib.request
import json

# Dictionary to keep track of running worker processes, indexed by port
WORKER_PROCESSES = {}

# Find the root path of our custom node to locate the worker script
ROOT_PATH = Path(__file__).parent.parent.parent.parent

class LegionProcessManager:
    @staticmethod
    def is_worker_alive(config):
        """
        Checks if a ComfyUI worker is responsive on its port.
        """
        host = config.get("host", "127.0.0.1")
        port = config.get("port")
        if port == 'auto':
            # For now, we can't check an 'auto' port that hasn't been assigned yet.
            # The logic will be more complex later.
            return False

        url = f"http://{host}:{port}/queue"
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    # We can even check the content if needed
                    # data = json.loads(response.read())
                    return True
        except Exception:
            return False
        return False

    @staticmethod
    def start_worker(config):
        """
        Starts a new ComfyUI worker as a local subprocess.
        """
        port = config.get("port")
        # A simple check to avoid trying to start a worker that's already managed
        if port in WORKER_PROCESSES and WORKER_PROCESSES[port].poll() is None:
            print(f"[LegionPower] Worker on port {port} is already managed and running.")
            return

        print(f"[LegionPower] Starting a new worker on port {port}...")

        worker_script_path = ROOT_PATH / "src" / "comfyui_legion_power" / "worker" / "launch_worker.py"

        # We need to use the same Python executable that is running ComfyUI
        python_executable = sys.executable

        command = [
            python_executable,
            str(worker_script_path),
            "--port", str(port),
        ]

        #if config.get("execution.force_cpu", False):
        #    command.append("--cpu-only")

        # More arguments like --comfyui-path will be added here later

        # Use Popen for non-blocking execution
        process = subprocess.Popen(command)
        WORKER_PROCESSES[port] = process

        print(f"[LegionPower] Worker process for port {port} launched with PID: {process.pid}.")

        # Wait a bit for the server to start before checking its status
        # This is a simple approach; a more robust one would poll until ready.
        print(f"[LegionPower] Waiting for worker on port {port} to come online...")
        time.sleep(10) # A generous wait time for the server to initialize

        if not LegionProcessManager.is_worker_alive(config):
            print(f"[LegionPower] WARNING: Worker on port {port} did not become responsive in time.")
        else:
            print(f"[LegionPower] Worker on port {port} is now online.")