import json
from pathlib import Path

class LegionJSONPatcher:
    def __init__(self, workflow_path: Path):
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found at: {workflow_path}")
        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)

    def patch(self, remote_arg: str, value):
        """
        Patch a value in the workflow JSON using dot notation.
        Auto-creates missing intermediate dictionaries.
        
        Example: patch("12.inputs.data_exchange_root", "/path/to/data")
        """
        try:
            keys = remote_arg.split('.')
            node_id = keys[0]

            # Ensure the node exists
            if node_id not in self.workflow:
                raise KeyError(f"Node '{node_id}' not found in workflow")

            target_dict = self.workflow[node_id]
            
            # Navigate/create intermediate keys
            for key in keys[1:-1]:
                if key not in target_dict:
                    # Auto-create missing intermediate dictionary
                    target_dict[key] = {}
                    print(f"[LegionPower] Created missing key '{key}' in path '{remote_arg}'")
                target_dict = target_dict[key]

            # Set the final value
            final_key = keys[-1]
            target_dict[final_key] = value
            print(f"[LegionPower] Patched workflow: Set '{remote_arg}' to '{value}'")
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"[LegionPower] WARNING: Could not patch workflow. Invalid remote_arg '{remote_arg}': {e}")
            raise

    def add_node(self, node_id: str, class_type: str, inputs: dict):
        """Adds a new node to the workflow."""
        if node_id in self.workflow:
            print(f"[LegionPower] WARNING: Node with ID '{node_id}' already exists. Overwriting.")

        self.workflow[node_id] = {
            "inputs": inputs,
            "class_type": class_type
        }
        print(f"[LegionPower] Patched workflow: Added node '{node_id}' of type '{class_type}'.")

    def get_patched_workflow(self):
        return self.workflow
