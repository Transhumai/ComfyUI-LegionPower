import yaml
from pathlib import Path
import folder_paths

COMFYUI_ROOT_PATH = Path(folder_paths.base_path)
LEGION_ROOT_PATH = COMFYUI_ROOT_PATH / "custom_nodes" / "ComfyUI-LegionPower" # <------- ho aggiunto questa in src/comfyui_legion_power/legion_config_manager.py perché mancava
LEGION_RUNTIME_PATH = COMFYUI_ROOT_PATH / "user" / "default" / "ComfyUI-LegionPower"

class LegionConfigManager:
    _instance = None
    _config = {}
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LegionConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    def _get_default_config(self):
        return {
            'ports': { 'start_port': 8200, 'max_workers': 20 },
            'paths': {
                'worker_templates_dir': str(LEGION_RUNTIME_PATH / 'ComfyUIs'),
                'workflows_roots': [ str(LEGION_RUNTIME_PATH / 'workflows'), str(COMFYUI_ROOT_PATH / 'workflows') ],
                'temp_root_dir': str(LEGION_RUNTIME_PATH / 'temp'),
            },
            'logging': { 'level': 'INFO' }
        }
    def _load_config(self):
        config_path = LEGION_RUNTIME_PATH / 'config.yaml'
        LEGION_RUNTIME_PATH.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            default_config = self._get_default_config()
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, sort_keys=False)
            self._config = default_config
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                self._config = loaded_config if loaded_config else self._get_default_config()
    def get(self, key_path, default=None):
        keys, value = key_path.split('.'), self._config
        for key in keys:
            if isinstance(value, dict) and key in value: value = value[key]
            else: return default
        return value

config_manager = LegionConfigManager()

def find_file_in_roots(filename: str, roots_key: str) -> Path:
    search_paths = config_manager.get(roots_key, [])
    if not isinstance(search_paths, list): search_paths = [search_paths]
    for root_str in search_paths:
        if not root_str: continue
        root_path = Path(root_str)
        root_path.mkdir(parents=True, exist_ok=True)
        target_file = root_path / filename
        if target_file.exists():
            print(f"[LegionPower] Found '{filename}' at: {target_file.resolve()}")
            return target_file.resolve()
    raise FileNotFoundError(f"Could not find '{filename}' in any of the configured '{roots_key}': {search_paths}")