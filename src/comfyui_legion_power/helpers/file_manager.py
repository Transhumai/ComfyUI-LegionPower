# src/comfyui_legion_power/helpers/file_manager.py
import uuid
from pathlib import Path
import shutil
from ..legion_config_manager import config_manager


class LegionFileManager:
    def __init__(self, run_id=None):
        self.temp_root = Path(config_manager.get("paths.temp_root_dir"))
        self.run_id = run_id if run_id else str(uuid.uuid4())
        self.run_path = self.temp_root / self.run_id

        # Non creiamo più le cartelle qui
        if not run_id:
            print(f"[LegionPower] FileManager initialized for NEW run ID: {self.run_id}")
            print(f"[LegionPower]  - Temp path: {self.run_path}")

    def _ensure_dir_exists(self, path: Path):
        """Helper function to create a directory only when needed."""
        path.parent.mkdir(parents=True, exist_ok=True)

    def get_input_path(self, local_arg_name: str, is_batch: bool = False):
        input_root = self.run_path / "inputs"
        if is_batch:
            path = input_root / local_arg_name
        else:
            filename = f"{local_arg_name}_{uuid.uuid4()}.png"
            path = input_root / filename

        # La directory viene creata qui, "just-in-time"
        self._ensure_dir_exists(path)
        return str(path.resolve())

    def get_output_path(self, local_arg_name: str, is_batch: bool = False):
        output_root = self.run_path / "outputs"
        if is_batch:
            path = output_root / local_arg_name
        else:
            filename = f"{local_arg_name}_{uuid.uuid4()}.png"
            path = output_root / filename

        # Anche qui, creata solo se la funzione viene chiamata
        self._ensure_dir_exists(path)
        return str(path.resolve())

    def cleanup(self):
        if self.run_path.exists():
            try:
                shutil.rmtree(self.run_path)
                print(f"[LegionPower] Cleaned up temp directory: {self.run_path}")
            except Exception as e:
                print(f"[LegionPower] ERROR: Failed to clean up temp directory {self.run_path}: {e}")
        else:
            print(f"[LegionPower] Cleanup skipped: Temp directory not found: {self.run_path}")