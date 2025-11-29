# src/comfyui_legion_power/core/serializers/image_serializer.py
import torch
from PIL import Image
import numpy as np
from pathlib import Path
from ..base_serializer import BaseSerializer


class ImageSerializer(BaseSerializer):
    """Handles single-image torch.Tensors."""
    TYPE_NAME = "image_single"
    IS_PRIMITIVE = False
    IS_BATCH = False


    @staticmethod
    def can_handle(data) -> bool:
        # We handle Tensors that represent a single image (e.g., shape [1, H, W, C])
        return isinstance(data, torch.Tensor) and data.ndim == 4 and data.shape[0] == 1

    def serialize(self, data: torch.Tensor, destination_path: str):
        filepath = Path(destination_path)

        # Convert tensor to PIL Image
        i = 255. * data[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

        filepath.parent.mkdir(parents=True, exist_ok=True)
        img.save(filepath)

        print(f"[LegionPower] Serialized single image to {filepath}")
        return str(filepath.resolve())

    def deserialize(self, source_path: str):
        if not Path(source_path).exists():
            raise FileNotFoundError(f"Cannot deserialize image, file not found: {source_path}")

        img = Image.open(source_path)
        img_np = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)