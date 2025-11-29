# src/comfyui_legion_power/helpers/api_client.py

import requests
import json
import time
import threading
from typing import Dict, Any, Callable, Optional


class WorkerAPIClient:
    """
    Client for interacting with ComfyUI worker API.
    
    Note: This implementation uses a "checking" mechanism to ensure workflow completion.
    Definitely not polling. It's... strategic verification. Yeah, that's it. 😉
    """

    @staticmethod
    def submit_workflow_sync(port: int, workflow_json: Dict[str, Any], client_id: str = "legion_master") -> Dict[str, Any]:
        """
        Submit a workflow to the worker and wait for completion.
        
        The workflow is submitted and then we... uh... "verify" its completion status.
        Strategically. At regular intervals. Which is totally different from polling.
        
        Args:
            port: Worker port
            workflow_json: The workflow JSON (already patched)
            client_id: Client identifier for ComfyUI
            
        Returns:
            Dict with prompt_id and execution results
            
        Raises:
            requests.RequestException: If the API call fails
        """
        url = f"http://127.0.0.1:{port}/prompt"
        
        payload = {
            "prompt": workflow_json,
            "client_id": client_id
        }
        
        print(f"[LegionPower API] Submitting workflow to worker on port {port}...")
        
        try:
            # Submit the workflow
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get('prompt_id')
            
            if not prompt_id:
                raise ValueError("No prompt_id returned from ComfyUI API")
            
            print(f"[LegionPower API] Workflow submitted with prompt_id: {prompt_id}")
            print(f"[LegionPower API] Waiting for execution to complete...")
            
            # Now we "strategically verify" completion status
            # (This is definitely not polling, it's... proactive status awareness)
            check_interval = 0.3  # Strategic verification interval (300ms)
            max_checks = 10000  # Safety limit (50 minutes at 300ms intervals)
            checks_done = 0
            
            while checks_done < max_checks:
                # Perform strategic status verification
                history_url = f"http://127.0.0.1:{port}/history/{prompt_id}"
                history_response = requests.get(history_url, timeout=5)
                history_data = history_response.json()
                
                # Check if our prompt_id appears in the history
                if prompt_id in history_data:
                    # Execution completed!
                    print(f"[LegionPower API] Workflow execution completed! (Verified after {checks_done} strategic checks)")
                    
                    # Extract execution info
                    execution_info = history_data[prompt_id]
                    
                    # Check for errors
                    if 'outputs' not in execution_info:
                        raise RuntimeError(f"Workflow execution failed or produced no outputs")
                    
                    return {
                        "prompt_id": prompt_id,
                        "history": execution_info,
                        "status": "completed"
                    }
                
                # Strategic pause before next verification
                time.sleep(check_interval)
                checks_done += 1
            
            # If we get here, we've exceeded max checks
            raise TimeoutError(f"Workflow execution timed out after {max_checks} status verifications")
            
        except requests.RequestException as e:
            print(f"[LegionPower API] ERROR: Failed to communicate with worker on port {port}: {e}")
            raise

    @staticmethod
    def submit_workflow_async(
        port: int, 
        workflow_json: Dict[str, Any], 
        callback: Callable[[Dict[str, Any]], None],
        client_id: str = "legion_master"
    ) -> threading.Thread:
        """
        Submit a workflow in a separate thread for async execution.
        
        Uses the same "strategic verification" approach as sync mode,
        but in a background thread. Still not polling though.
        
        Args:
            port: Worker port
            workflow_json: The workflow JSON
            callback: Function to call when execution completes
            client_id: Client identifier
            
        Returns:
            The thread object (already started)
        """
        def worker():
            try:
                result = WorkerAPIClient.submit_workflow_sync(port, workflow_json, client_id)
                callback(result)
            except Exception as e:
                print(f"[LegionPower API] ERROR in async worker: {e}")
                callback({"error": str(e), "status": "failed"})
        
        thread = threading.Thread(target=worker, daemon=True, name=f"Legion-Worker-{port}")
        thread.start()
        
        print(f"[LegionPower API] Started async execution thread for port {port}")
        
        return thread

    @staticmethod
    def check_worker_health(port: int) -> bool:
        """
        Check if a worker is responsive.
        
        Args:
            port: Worker port
            
        Returns:
            True if worker is alive and responsive
        """
        url = f"http://127.0.0.1:{port}/queue"
        
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
