from abc import ABC, abstractmethod

class BaseSerializer(ABC):
    """
    Abstract base class for data serializers.
    Defines the contract for serializing (saving) and deserializing (loading) data.
    """

    @staticmethod
    @abstractmethod
    def can_handle(data) -> bool:
        """
        Returns True if this serializer can handle the given data type.
        """
        pass

    @abstractmethod
    def serialize(self, data, destination_path: str):
        """
        Serializes the data to a specified destination.
        For file-based serializers, this is a file path.
        For primitive types, this might just return the value itself.

        Returns the value that should be injected into the remote workflow's JSON.
        (e.g., a file path for images, or the primitive value itself).
        """
        pass

    @abstractmethod
    def deserialize(self, source_path: str):
        """
        Deserializes data from a source.
        For file-based serializers, this is a file path.
        """
        pass