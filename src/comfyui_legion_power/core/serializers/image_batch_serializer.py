# src/comfyui_legion_power/core/serializers/image_batch_serializer.py
import torch
from PIL import Image
import numpy as np
from pathlib import Path
from ..base_serializer import BaseSerializer


class ImageBatchSerializer(BaseSerializer):
    """
    Handles a batch of images in a single torch.Tensor.
    Serializes them into a numbered sequence of files in a directory.
    """
    TYPE_NAME = "image_batch"
    IS_PRIMITIVE = False
    IS_BATCH = True


    @staticmethod
    def can_handle(data) -> bool:
        # We handle Tensors that represent a batch of images (e.g., shape [B, H, W, C] where B >= 1)
        return isinstance(data, torch.Tensor) and data.ndim == 4 and data.shape[0] >= 1


    def serialize(self, data: torch.Tensor, destination_path: str):
        dir_path = Path(destination_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        for i, tensor_slice in enumerate(data):
            img_np = 255. * tensor_slice.cpu().numpy()
            img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8))

            # Save as a numbered sequence, e.g., 0001.png, 0002.png
            filepath = dir_path / f"{i:04d}.png"
            img.save(filepath)

        print(f"[LegionPower] Serialized image batch of {len(data)} images to directory {dir_path}")
        # The value to inject is the path to the directory
        return str(dir_path.resolve())

    def deserialize(self, source_path: str):
        dir_path = Path(source_path)

        if not dir_path.is_dir():
            raise FileNotFoundError(f"Cannot deserialize image batch, directory not found: {source_path}")

        images = []
        # Find all png files and sort them numerically
        files = sorted(dir_path.glob("*.png"))

        for filepath in files:
            img = Image.open(filepath)
            img_np = np.array(img).astype(np.float32) / 255.0
            images.append(torch.from_numpy(img_np))

        if not images:
            raise ValueError(f"No PNG images found in directory: {source_path}")

        batch = torch.stack(images)

        return batch