# src/comfyui_legion_power/core/serializers/image_serializer.py
import torch
from PIL import Image
import numpy as np
from pathlib import Path
from ..base_serializer import BaseSerializer


class ImageSerializer(BaseSerializer):
    """
    Handles single-image torch.Tensors.

    Optimizations:
    - Handles RGB (3 channels) and RGBA (4 channels) automatically
    - Uses PNG with compression=0 for maximum speed (temporary files)
    """
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
        img_np = 255. * data[0].cpu().numpy()
        img_np_clipped = np.clip(img_np, 0, 255).astype(np.uint8)

        # Automatically detect RGB vs RGBA based on shape
        if img_np_clipped.shape[2] == 3:
            img = Image.fromarray(img_np_clipped, mode='RGB')
        elif img_np_clipped.shape[2] == 4:
            img = Image.fromarray(img_np_clipped, mode='RGBA')
        else:
            # Fallback: let PIL auto-detect
            img = Image.fromarray(img_np_clipped)

        filepath.parent.mkdir(parents=True, exist_ok=True)

        # compress_level=0 = NO compression for maximum speed
        img.save(filepath, compress_level=0)

        print(f"[LegionPower] Serialized single image to {filepath}")
        return str(filepath.resolve())

    def deserialize(self, source_path: str):
        if not Path(source_path).exists():
            raise FileNotFoundError(f"Cannot deserialize image, file not found: {source_path}")

        img = Image.open(source_path)

        # Convert to numpy, preserving alpha channel if present
        img_np = np.array(img).astype(np.float32) / 255.0

        # Add batch dimension: [H, W, C] -> [1, H, W, C]
        return torch.from_numpy(img_np).unsqueeze(0)