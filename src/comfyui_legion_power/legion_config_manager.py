import yaml
from pathlib import Path
import folder_paths

COMFYUI_ROOT_PATH = Path(folder_paths.base_path)
LEGION_ROOT_PATH = COMFYUI_ROOT_PATH / "custom_nodes" / "ComfyUI-LegionPower"
LEGION_RUNTIME_PATH = COMFYUI_ROOT_PATH / "user" / "default" / "ComfyUI-LegionPower"

class LegionConfigManager:
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LegionConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """
        Load config.yaml from runtime path.
        If not found, copy template from LEGION_ROOT_PATH/runtime/config.yaml
        """
        config_path = LEGION_RUNTIME_PATH / 'config.yaml'
        template_path = LEGION_ROOT_PATH / "runtime" / "config.yaml"

        # Ensure runtime directory exists
        LEGION_RUNTIME_PATH.mkdir(parents=True, exist_ok=True)

        # Try runtime path first
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                self._config = loaded_config if loaded_config else {}
        else:
            # If not exists, try template
            if template_path.exists():
                print(f"[LegionPower] Using template config from: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_config = yaml.safe_load(f)

                # Copy template to runtime path for future use
                print(f"[LegionPower] Copying config template to: {config_path}")
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(template_config, f, sort_keys=False)

                self._config = template_config
            else:
                # Fallback: hardcoded default (should never happen in normal installation)
                print(f"[LegionPower] WARNING: No config template found, using hardcoded defaults")
                self._config = self._get_hardcoded_fallback()

                # Save fallback to runtime path
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, sort_keys=False)

    def _get_hardcoded_fallback(self):
        """
        Hardcoded fallback config (only used if template is missing)
        """
        return {
            'ports': {
                'start_port': 8200,
                'max_workers': 20
            },
            'worker': {
                'startup_timeout': 300
            },
            'paths': {
                'worker_templates_dir': str(LEGION_RUNTIME_PATH / 'ComfyUIs'),
                'workflows_roots': [
                    str(LEGION_RUNTIME_PATH / 'workflows'),
                    str(COMFYUI_ROOT_PATH / 'workflows')
                ],
                'temp_root_dir': str(LEGION_RUNTIME_PATH / 'temp'),
            },
            'logging': {
                'level': 'INFO'
            }
        }

    def get(self, key_path, default=None):
        """
        Get a config value using dot notation.
        Example: get('ports.start_port', 8200)
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

# Singleton instance
config_manager = LegionConfigManager()

def find_file_in_roots(filename: str, roots_key: str) -> Path:
    """
    Search for a file in configured root paths.

    Args:
        filename: Name of file to find
        roots_key: Config key for list of root paths (e.g., 'paths.workflows_roots')

    Returns:
        Resolved Path to the file

    Raises:
        FileNotFoundError: If file not found in any root
    """
    search_paths = config_manager.get(roots_key, [])

    if not isinstance(search_paths, list):
        search_paths = [search_paths]

    for root_str in search_paths:
        if not root_str:
            continue

        root_path = Path(root_str)
        root_path.mkdir(parents=True, exist_ok=True)

        target_file = root_path / filename
        if target_file.exists():
            print(f"[LegionPower] Found '{filename}' at: {target_file.resolve()}")
            return target_file.resolve()

    raise FileNotFoundError(
        f"Could not find '{filename}' in any of the configured '{roots_key}': {search_paths}"
    )