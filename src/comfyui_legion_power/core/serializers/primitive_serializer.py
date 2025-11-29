# src/comfyui_legion_power/core/serializers/primitive_serializer.py
from ..base_serializer import BaseSerializer

SUPPORTED_PRIMITIVES = (str, int, float, bool)

class PrimitiveSerializer(BaseSerializer):
    """Handles primitive data types that are JSON-safe."""
    TYPE_NAME = "primitive"
    IS_PRIMITIVE = True
    IS_BATCH = False

    @staticmethod
    def can_handle(data) -> bool:
        return isinstance(data, SUPPORTED_PRIMITIVES)

    def serialize(self, data, destination_path: str):
        # Primitive types don't need to be saved to a file.
        # The value to be injected is the data itself.
        print(f"[LegionPower] Serializing primitive value: {data}")
        return data

    def deserialize(self, source_path: str):
        # This should not be called for primitives, as they are passed directly.
        # But we implement it for completeness.
        # The 'source_path' in this case would be the value itself.
        return source_path