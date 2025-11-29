# src/comfyui_legion_power/nodes/legion_importer.py

from pathlib import Path
import json
from ..core.legion_datatypes import any
from ..core.serializer_manager import SERIALIZER_CLASSES


class LegionImporterNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # The Master will patch this value in the workflow JSON
                "data_exchange_root": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = (any, any, any, any, any, "STRING")
    RETURN_NAMES = ("output_1", "output_2", "output_3", "output_4", "output_5", "data_exchange_root")
    FUNCTION = "import_data"
    CATEGORY = "Legion/IO"

    def import_data(self, data_exchange_root):
        print(f"[Legion Importer] Starting import from: {data_exchange_root}")

        # data_exchange_root already points to the run-specific directory (e.g., temp/{run_id}/)
        run_path = Path(data_exchange_root)
        manifest_path = run_path / "inputs" / "manifest_input.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Input manifest not found! Expected at: {manifest_path}")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        print(f"[Legion Importer] Loaded input manifest from: {manifest_path}")

        deserialized_outputs = {}

        # Create a mapping from TYPE_NAME to the serializer class for quick lookup
        serializer_map = {s.TYPE_NAME: s for s in SERIALIZER_CLASSES}

        for name, info in manifest.items():
            output_data = None
            serializer_type = info.get("type")

            if serializer_type not in serializer_map:
                print(f"[Legion Importer] WARNING: Unknown serializer type '{serializer_type}' for input '{name}'. Skipping.")
                continue

            # Get an instance of the correct deserializer
            deserializer = serializer_map[serializer_type]()

            if "value" in info:
                # Primitive type, the value is in the manifest itself
                output_data = deserializer.deserialize(info["value"])
                print(f"[Legion Importer]  - Deserialized primitive '{name}': {output_data}")
            elif "path" in info:
                # File-based type
                source_path = run_path / "inputs" / info["path"]
                output_data = deserializer.deserialize(str(source_path.resolve()))
                print(f"[Legion Importer]  - Deserialized '{name}' from path: {source_path}")

            deserialized_outputs[name] = output_data

        # Map input_X to output_X
        # The Master serializes as input_1, input_2, etc.
        # But we need to return them as output_1, output_2, etc.
        final_outputs = (
            deserialized_outputs.get("input_1"),  # Maps to output_1
            deserialized_outputs.get("input_2"),  # Maps to output_2
            deserialized_outputs.get("input_3"),  # Maps to output_3
            deserialized_outputs.get("input_4"),  # Maps to output_4
            deserialized_outputs.get("input_5"),  # Maps to output_5
            data_exchange_root,  # Passthrough for LegionExporter
        )

        return final_outputs
