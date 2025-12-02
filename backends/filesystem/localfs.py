import os
from pathlib import Path

from backends.filesystem.abstractfs import AbstractFileSystem


class LocalFileSystem(AbstractFileSystem):
    """Local file system implementation of the FileSystemInterface."""

    def __init__(self, root: str = '.'):
        self.root = Path(root)
        if not self.root.exists():
            self.root.mkdir(parents=True)

    def read(self, relative_path: str):
        """Read data from the local file."""
        path = self.root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"The file '{relative_path}' does not exist.")
        if not path.is_file():
            raise TypeError(f"The file '{relative_path}' is not a file.")
        
        with open(self.root / relative_path, 'rb') as file:
            return file.read()

    def write(self, relative_path: str, data: bytes):
        """Write data to the local file."""
        with open(self.root / relative_path, 'wb') as file:
            file.write(data)

    def list(self, relative_dir: str):
        """List files in the specified directory."""
        return os.listdir(self.root / relative_dir)

    def delete(self, relative_path: str):
        """Delete the file."""
        (self.root / relative_path).unlink(missing_ok=True)
