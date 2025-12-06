# src/comfyui_legion_power/nodes/legion_exporter.py

import os
from pathlib import Path
import json
from ..core.legion_datatypes import any
from ..core.serializer_manager import get_serializer_for_data
from ..legion_config_manager import LEGION_RUNTIME_PATH


class LegionExporterNode:
    # This node is a terminal node; it doesn't have outputs in the ComfyUI sense
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # Receives this from LegionImporter's passthrough output
                "data_exchange_root": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "input_1": (any,), "input_2": (any,),
                "input_3": (any,), "input_4": (any,),
                "input_5": (any,),
            }
        }

    # This node doesn't return anything to the workflow
    RETURN_TYPES = ()
    FUNCTION = "export_data"
    CATEGORY = "Legion/IO"

    def export_data(self, data_exchange_root, **kwargs):
        print(f"[Legion Exporter] Starting export to: {data_exchange_root}")

        # Base directory considered safe (current non-configurable behavior)
        allowed_root = (LEGION_RUNTIME_PATH / "temp").resolve()

        # data_exchange_root already points to the run-specific directory
        run_path = Path(data_exchange_root).resolve()
        outputs_path = (run_path / "outputs").resolve()

        # SECURITY CHECK — using commonpath after resolving handles symlinks/junctions safely
        if os.path.commonpath([str(allowed_root), str(outputs_path)]) != str(allowed_root):
            raise ValueError(
                f"[Legion Exporter] ERROR: Output path '{outputs_path}' is outside allowed directory '{allowed_root}'."
            )

        outputs_path.mkdir(parents=True, exist_ok=True)

        manifest = {}

        # Process all connected inputs (input_1, input_2, etc.)
        for name, data in kwargs.items():
            if data is None:
                continue

            print(f"[Legion Exporter] Processing input '{name}'...")
            serializer = get_serializer_for_data(data)

            if serializer is None:
                print(f"[Legion Exporter] WARNING: Unsupported data type for input '{name}' ({type(data).__name__}). Skipping.")
                continue

            # For primitives, the value is stored directly in the manifest
            if getattr(serializer, 'IS_PRIMITIVE', False):
                value = serializer.serialize(data, "") # Path is not needed
                manifest[name] = {
                    "type": serializer.TYPE_NAME,
                    "value": value
                }
                print(f"[Legion Exporter]  - Stored primitive value: {value}")
            else:
                # For file-based types, we serialize to a subfolder
                output_subpath = Path(outputs_path / name).resolve()

                # SECURITY CHECK — using commonpath after resolving handles symlinks/junctions safely
                if os.path.commonpath([str(allowed_root), str(output_subpath)]) != str(allowed_root):
                    raise ValueError(
                        f"[Legion Exporter] ERROR: Output path '{output_subpath}' is outside allowed directory '{allowed_root}'."
                    )

                # The serializer will save the data to the given path
                serializer.serialize(data, output_subpath)

                manifest[name] = {
                    "type": serializer.TYPE_NAME,
                    "path": name # Relative path within the 'outputs' directory
                }
                print(f"[Legion Exporter]  - Serialized data to subfolder: {name}")

        # Write the final manifest file
        manifest_path = run_path / "outputs" / "manifest_output.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"[Legion Exporter] Output manifest written to: {manifest_path}")

        return {} # Must return a dictionary
