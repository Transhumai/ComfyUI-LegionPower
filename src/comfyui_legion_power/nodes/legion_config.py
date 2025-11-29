import yaml
from ..core.legion_datatypes import LegionConfig

from ..legion_config_manager import LEGION_RUNTIME_PATH, LEGION_ROOT_PATH


def load_default_template():
    template_path = LEGION_RUNTIME_PATH / "default_legion_config.yaml"
    fallback_path = LEGION_ROOT_PATH / "runtime" / "default_legion_config.yaml"

    res = "..." # (default content stays the same)

    # Try runtime path first
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            res = f.read().strip()
    else:
        # If not exists, try fallback
        if fallback_path.exists():
            print(f"[LegionPower] Using fallback template from: {fallback_path}")
            with open(fallback_path, 'r', encoding='utf-8') as f:
                res = f.read().strip()

            # Save template to template_path for future use
            template_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[LegionPower] Copying template to: {template_path}")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(res)

    #print(f"Template is: {res}")
    return res


class LegionConfigNode:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "config_yaml": ("STRING", {"default": load_default_template(), "multiline": True}),
            }
        }

    RETURN_TYPES = ("LEGION_CONFIG",)
    RETURN_NAMES = ("legion_config",)
    FUNCTION = "create_config"
    CATEGORY = "Legion"

    def create_config(self, config_yaml):
        try:
            user_config_dict = yaml.safe_load(config_yaml)
            if not isinstance(user_config_dict, dict):
                raise ValueError("YAML must represent a dictionary (key-value map).")
        except Exception as e:
            print(f"[LegionPower] ERROR: Invalid YAML configuration: {e}")
            # Returning (None,) will stop the workflow execution at this node
            return (None,)

        config = LegionConfig(**user_config_dict)
        return (config,)