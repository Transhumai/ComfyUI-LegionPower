# src/comfyui_legion_power/core/serializer_manager.py

from .serializers.primitive_serializer import PrimitiveSerializer
from .serializers.image_serializer import ImageSerializer
from .serializers.image_batch_serializer import ImageBatchSerializer

# A list of all available serializer classes.
# The order is important: more specific handlers should come first.
SERIALIZER_CLASSES = [
    ImageBatchSerializer,
    ImageSerializer,
    PrimitiveSerializer,
]

def get_serializer_for_data(data):
    """
    Finds and returns an instance of the appropriate serializer for the given data.
    """
    for serializer_class in SERIALIZER_CLASSES:
        if serializer_class.can_handle(data):
            return serializer_class() # Return an instance of the class

    return None # No suitable serializer found