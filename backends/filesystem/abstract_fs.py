from abc import ABC, abstractmethod


class AbstractFileSystem(ABC):
    """Abstract base class for file system operations."""

    @abstractmethod
    def read(self, relative_path: str):
        """Read data from the file."""
        pass

    @abstractmethod
    def write(self, relative_path: str, data: bytes):
        """Write data to the file."""
        pass

    @abstractmethod
    def list(self, relative_dir: str):
        """List files in the specified directory."""
        pass

    @abstractmethod
    def delete(self, relative_path: str):
        """Delete the file."""
        pass