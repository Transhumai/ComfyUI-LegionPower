# src/comfyui_legion_power/nodes/legion_join.py

import json
from pathlib import Path
from ..core.legion_datatypes import LEGION_CAMPAIGN, any
from ..core.serializer_manager import SERIALIZER_CLASSES


class LegionJoinNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "legion_campaign": (LEGION_CAMPAIGN,),
            }
        }

    RETURN_TYPES = (any, any, any, any, any)
    RETURN_NAMES = ("output_1", "output_2", "output_3", "output_4", "output_5")
    FUNCTION = "join_campaign"
    CATEGORY = "Legion"

    def join_campaign(self, legion_campaign):
        print(f"[Legion Join] Joining campaign: {legion_campaign.campaign_id}")

        # Check if campaign was async
        is_async = legion_campaign.config.get("execution.asynch", False)

        if not is_async:
            # Sync campaign: outputs should be stored in campaign object
            print(f"[Legion Join] Campaign is SYNC mode - reading outputs from campaign object")

            if hasattr(legion_campaign, 'outputs'):
                # Outputs were stored by Master in sync mode
                outputs = legion_campaign.outputs
                print(f"[Legion Join] Retrieved {len([o for o in outputs if o is not None])} outputs from campaign")
                return outputs[:5]  # Return first 5 outputs
            else:
                # Fallback: this shouldn't happen in normal flow
                print(f"[Legion Join] WARNING: Sync campaign has no stored outputs!")
                return (None, None, None, None, None)

        # Async campaign: wait for execution thread and read from files
        if hasattr(legion_campaign, 'execution_thread') and legion_campaign.execution_thread:
            print(f"[Legion Join] Waiting for async execution to complete...")
            legion_campaign.execution_thread.join()  # Block until thread completes
            print(f"[Legion Join] Async execution completed!")

        # Check campaign status
        if legion_campaign.status == "FAILED":
            raise RuntimeError(f"Campaign {legion_campaign.campaign_id} failed during execution")

        if legion_campaign.status not in ["COMPLETED", "DRY_RUN_COMPLETE"]:
            raise RuntimeError(f"Campaign {legion_campaign.campaign_id} has unexpected status: {legion_campaign.status}")

        # Deserialize outputs from manifest
        from ..helpers.file_manager import LegionFileManager
        file_manager = LegionFileManager(run_id=legion_campaign.campaign_id)

        output_manifest_path = file_manager.run_path / "outputs" / "manifest_output.json"

        if not output_manifest_path.exists():
            print(f"[Legion Join] WARNING: Output manifest not found at {output_manifest_path}")
            print(f"[Legion Join] Returning None outputs")
            final_outputs = (None, None, None, None, None)
        else:
            with open(output_manifest_path, 'r', encoding='utf-8') as f:
                output_manifest = json.load(f)

            deserialized_outputs = {}
            serializer_map = {s.TYPE_NAME: s for s in SERIALIZER_CLASSES}

            for name, info in output_manifest.items():
                serializer_type = info.get("type")

                if serializer_type not in serializer_map:
                    print(f"[Legion Join] WARNING: Unknown serializer type '{serializer_type}' for output '{name}'")
                    continue

                deserializer = serializer_map[serializer_type]()

                if "value" in info:
                    # Primitive type
                    deserialized_outputs[name] = deserializer.deserialize(info["value"])
                    print(f"[Legion Join]  - Deserialized primitive '{name}'")
                elif "path" in info:
                    # File-based type
                    source_path = file_manager.run_path / "outputs" / info["path"]
                    deserialized_outputs[name] = deserializer.deserialize(str(source_path.resolve()))
                    print(f"[Legion Join]  - Deserialized '{name}' from path")

            # Note: LegionExporter uses input_X naming for its inputs
            final_outputs = (
                deserialized_outputs.get("input_1"),
                deserialized_outputs.get("input_2"),
                deserialized_outputs.get("input_3"),
                deserialized_outputs.get("input_4"),
                deserialized_outputs.get("input_5"),
            )

        # Cleanup
        file_manager.cleanup()

        return final_outputs