# src/comfyui_legion_power/core/legion_datatypes.py
import yaml


class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __eq__(self, _) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False


class LegionConfig:
    """
    A simple data class to hold all settings for a worker, parsed from YAML.
    This object is passed between Legion nodes.
    """
    def __init__(self, **kwargs):
        self.raw_config = kwargs

    def get(self, key_path, default=None):
        """
        Retrieves a value from the configuration using a dot-separated path, e.g., 'execution.force_cpu'.
        """
        keys = key_path.split('.')
        value = self.raw_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def __repr__(self):
        # Provides a nice string representation for debugging purposes
        return f"LegionConfig({yaml.dump(self.raw_config, indent=2)})"


class LegionCampaign:
    """
    An object representing a dispatched workflow execution. It holds all state
    related to a single run, including its config, ID, status, and output paths.
    """

    def __init__(self, campaign_id=None, config=None, status="CREATED"):
        import uuid
        self.campaign_id = campaign_id if campaign_id else str(uuid.uuid4())
        self.config = config # This will be a LegionConfig object
        self.status = status
        self.outputs = {} # dict mapping here_arg_name to its future file path

        # This will hold the final resolved port after 'auto' is handled
        self.resolved_port = None

    def __repr__(self):
        return f"LegionCampaign(id={self.campaign_id}, status={self.status}, port={self.resolved_port})"


# Add types at the end of the file
LEGION_CAMPAIGN = "LEGION_CAMPAIGN"
LEGION_CONFIG = "LEGION_CONFIG"
any = AnyType("*")