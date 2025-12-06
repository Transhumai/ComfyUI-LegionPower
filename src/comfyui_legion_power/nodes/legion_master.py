# src/comfyui_legion_power/nodes/legion_master.py

import json
from pathlib import Path

# Internal imports
from ..core.legion_datatypes import LEGION_CONFIG, LEGION_CAMPAIGN, any, LegionCampaign
from ..helpers.worker_manager import LegionWorkerManager
from ..helpers.file_manager import LegionFileManager
from ..core.serializer_manager import get_serializer_for_data


class LegionMasterNode:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "legion_config": (LEGION_CONFIG,),
                "legion_campaign": (LEGION_CAMPAIGN,),
                "input_1": (any,), "input_2": (any,), "input_3": (any,),
                "input_4": (any,), "input_5": (any,), "input_6": (any,),
                "input_7": (any,), "input_8": (any,), "input_9": (any,),
                "input_10": (any,), "input_11": (any,), "input_12": (any,),
            }
        }

    RETURN_TYPES = (LEGION_CAMPAIGN, any, any, any, any, any, any, any, any, any, any, any, any)
    RETURN_NAMES = ("legion_campaign", "output_1", "output_2", "output_3", "output_4", "output_5", "output_6", "output_7", "output_8", "output_9", "output_10", "output_11", "output_12")
    FUNCTION = "execute"
    CATEGORY = "Legion"

    def execute(self, legion_config=None, legion_campaign=None, just_warmup=False, **kwargs):

        err_root = "Master Node requires either a 'legion_config' or a 'legion_campaign' input"

        if legion_config is None and legion_campaign is None:
            raise ValueError(f"{err_root}.")

        if legion_config is not None and legion_campaign is not None:
            raise ValueError(f"{err_root}, not both!")

        # 1. Determine Config (reuse from campaign if provided, otherwise use legion_config)
        config = legion_campaign.config if legion_campaign else legion_config

        # ALWAYS create a new campaign for each execution to avoid state reuse
        campaign = LegionCampaign(config=config)

        # Cleanup old output references from previous executions (if any exist in memory)
        # This allows Python's GC to free memory from previous runs
        if legion_campaign and hasattr(legion_campaign, 'outputs'):
            legion_campaign.outputs = None  # Release reference to old outputs

        # 2. Ensure Worker is Alive
        LegionWorkerManager.ensure_worker_is_alive(campaign)
        campaign.status = "WARMED_UP"

        if just_warmup:
            print(f"[LegionPower] Warmup complete for campaign {campaign.campaign_id} on port {campaign.resolved_port}")
            return (campaign,) + (None,) * 12

        # --- Execution Logic ---
        dry_run = campaign.config.get("execution.dry_run", False)

        print(f"\n--- [LegionPower] Preparing Campaign {campaign.campaign_id} ---")

        file_manager = LegionFileManager(run_id=campaign.campaign_id)
        local_inputs = {key: value for key, value in kwargs.items() if value is not None and key.startswith("input_")}

        # 4. Serialize all provided inputs and create the input manifest
        input_manifest = {}
        for here_arg_name, data in local_inputs.items():
            serializer = get_serializer_for_data(data)
            if serializer is None:
                print(f"[LegionPower] WARNING: No serializer for input '{here_arg_name}' (type: {type(data).__name__}). Skipping.")
                continue

            print(f"[LegionPower] Serializing input '{here_arg_name}'...")
            is_batch = getattr(serializer, 'IS_BATCH', False)

            destination_path_str = file_manager.get_input_path(here_arg_name, is_batch=is_batch)
            manifest_value = serializer.serialize(data, Path(destination_path_str))

            if getattr(serializer, 'IS_PRIMITIVE', False):
                input_manifest[here_arg_name] = {"type": getattr(serializer, 'TYPE_NAME', 'unknown'), "value": manifest_value}
            else:
                input_manifest[here_arg_name] = {"type": getattr(serializer, 'TYPE_NAME', 'unknown'), "path": here_arg_name}

        # 5. Write the manifest file
        manifest_path = file_manager.run_path / "inputs" / "manifest_input.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(input_manifest, f, indent=2)
        print(f"[LegionPower] Input manifest written to: {manifest_path}")

        if dry_run:
            print("\n--- [LegionPower] Dry Run Complete ---")
            print(" - Input data has been serialized to the temp directory.")
            print(" - In a real run, the worker would now be executed.")

            campaign.status = "DRY_RUN_COMPLETE"

            # For dry_run, we just pass through the inputs to the outputs
            simulated_outputs = (
                campaign,
                kwargs.get("input_1"),
                kwargs.get("input_2"),
                kwargs.get("input_3"),
                kwargs.get("input_4"),
                kwargs.get("input_5"),
                kwargs.get("input_6"),
                kwargs.get("input_7"),
                kwargs.get("input_8"),
                kwargs.get("input_9"),
                kwargs.get("input_10"),
                kwargs.get("input_11"),
                kwargs.get("input_12"),
            )

            # We clean up immediately in a dry run
            file_manager.cleanup()

            return simulated_outputs

        # --- REAL EXECUTION ---
        from ..helpers.json_patcher import LegionJSONPatcher
        from ..helpers.api_client import WorkerAPIClient
        from ..legion_config_manager import find_file_in_roots

        # 6. Load and patch the workflow
        workflow_filename = campaign.config.get("workflow")
        if not workflow_filename:
            raise ValueError("No workflow specified in legion config!")

        workflow_path = find_file_in_roots(workflow_filename, "paths.workflows_roots")
        patcher = LegionJSONPatcher(workflow_path)

        # Find the LegionImporter node and patch its data_exchange_root
        importer_node_id = None
        for node_id, node_data in patcher.workflow.items():
            if node_data.get("class_type") == "LegionImporter":
                importer_node_id = node_id
                break

        if not importer_node_id:
            raise ValueError(f"Workflow '{workflow_filename}' must contain a 'LegionImporter' node!")

        # Patch the data_exchange_root value
        data_exchange_root_path = str(file_manager.run_path.resolve())
        patcher.patch(f"{importer_node_id}.inputs.data_exchange_root", data_exchange_root_path)

        patched_workflow = patcher.get_patched_workflow()

        # 7. Determine execution mode (sync vs async)
        is_async = campaign.config.get("execution.asynch", False)

        if is_async:
            # Async mode: start thread and return immediately with None outputs
            print(f"[LegionPower] Starting ASYNC execution on port {campaign.resolved_port}...")

            def async_callback(result):
                if "error" in result:
                    print(f"[LegionPower] ASYNC execution FAILED: {result['error']}")
                    campaign.status = "FAILED"
                else:
                    print(f"[LegionPower] ASYNC execution COMPLETED for campaign {campaign.campaign_id}")
                    campaign.status = "COMPLETED"

            thread = WorkerAPIClient.submit_workflow_async(
                campaign.resolved_port,
                patched_workflow,
                async_callback
            )

            campaign.execution_thread = thread
            campaign.status = "EXECUTING_ASYNC"

            # Return error message instead of None to help users understand they need Join
            error_msg = "ERROR: async is True! Get the outputs from a 'Legion: Join' node, please!"
            return (campaign,) + (error_msg,) * 12

        else:
            # Sync mode: block until completion
            print(f"[LegionPower] Starting SYNC execution on port {campaign.resolved_port}...")

            try:
                api_result = WorkerAPIClient.submit_workflow_sync(
                    campaign.resolved_port,
                    patched_workflow
                )

                campaign.status = "COMPLETED"
                print(f"[LegionPower] SYNC execution COMPLETED for campaign {campaign.campaign_id}")

                # 8. Deserialize outputs
                output_manifest_path = file_manager.run_path / "outputs" / "manifest_output.json"

                if not output_manifest_path.exists():
                    print(f"[LegionPower] WARNING: Output manifest not found at {output_manifest_path}")
                    final_outputs = (campaign,) + (None,) * 12
                else:
                    with open(output_manifest_path, 'r', encoding='utf-8') as f:
                        output_manifest = json.load(f)

                    deserialized_outputs = {}
                    from ..core.serializer_manager import SERIALIZER_CLASSES
                    serializer_map = {s.TYPE_NAME: s for s in SERIALIZER_CLASSES}

                    for name, info in output_manifest.items():
                        serializer_type = info.get("type")

                        if serializer_type not in serializer_map:
                            print(f"[LegionPower] WARNING: Unknown serializer type '{serializer_type}' for output '{name}'")
                            continue

                        deserializer = serializer_map[serializer_type]()

                        if "value" in info:
                            # Primitive type
                            deserialized_outputs[name] = deserializer.deserialize(info["value"])
                        elif "path" in info:
                            # File-based type
                            source_path = file_manager.run_path / "outputs" / info["path"]
                            deserialized_outputs[name] = deserializer.deserialize(str(source_path.resolve()))

                    final_outputs = (
                        campaign,
                        deserialized_outputs.get("input_1"),  # Note: exporter uses input_X naming
                        deserialized_outputs.get("input_2"),
                        deserialized_outputs.get("input_3"),
                        deserialized_outputs.get("input_4"),
                        deserialized_outputs.get("input_5"),
                        deserialized_outputs.get("input_6"),
                        deserialized_outputs.get("input_7"),
                        deserialized_outputs.get("input_8"),
                        deserialized_outputs.get("input_9"),
                        deserialized_outputs.get("input_10"),
                        deserialized_outputs.get("input_11"),
                        deserialized_outputs.get("input_12"),
                    )

                    # In SYNC mode, store outputs in campaign for potential Join node
                    # This allows Join to retrieve outputs even after cleanup
                    campaign.outputs = final_outputs[1:]  # Exclude campaign itself from outputs

                # Cleanup
                file_manager.cleanup()

                return final_outputs

            except Exception as e:
                campaign.status = "FAILED"
                print(f"[LegionPower] ERROR during execution: {e}")
                import traceback
                traceback.print_exc()
                raise


class LegionMasterNode3(LegionMasterNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "legion_config": (LEGION_CONFIG,),
                "legion_campaign": (LEGION_CAMPAIGN,),
                "input_1": (any,), "input_2": (any,), "input_3": (any,),
            }
        }

    RETURN_TYPES = (LEGION_CAMPAIGN, any, any, any)
    RETURN_NAMES = ("legion_campaign", "output_1", "output_2", "output_3")
    FUNCTION = "execute2"
    CATEGORY = "Legion"

    def execute2(self, legion_config=None, legion_campaign=None, **kwargs):
        return self.execute(legion_config=legion_config, legion_campaign=legion_campaign, just_warmup=False, **kwargs)


class LegionMasterNode6(LegionMasterNode):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "legion_config": (LEGION_CONFIG,),
                "legion_campaign": (LEGION_CAMPAIGN,),
                "input_1": (any,), "input_2": (any,), "input_3": (any,),
                "input_4": (any,), "input_5": (any,), "input_6": (any,),
            }
        }

    RETURN_TYPES = (LEGION_CAMPAIGN, any, any, any, any, any, any)
    RETURN_NAMES = ("legion_campaign", "output_1", "output_2", "output_3", "output_4", "output_5", "output_6")
    FUNCTION = "execute2"
    CATEGORY = "Legion"

    def execute2(self, legion_config=None, legion_campaign=None, **kwargs):
        return self.execute(legion_config=legion_config, legion_campaign=legion_campaign, just_warmup=False, **kwargs)