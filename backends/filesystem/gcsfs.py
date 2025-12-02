from google.cloud import storage
from backends.filesystem.abstractfs import AbstractFileSystem


class GCSFileSystem(AbstractFileSystem):
    """Google Cloud Storage implementation of the FileSystemInterface."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def read(self, relative_path: str) -> bytes:
        """Read data from a GCS file."""
        blob = self.bucket.blob(relative_path)
        if not blob.exists():
            raise FileNotFoundError(f"The file '{relative_path}' does not exist in the GCS bucket.")
        return blob.download_as_bytes()

    def write(self, relative_path: str, data: bytes):
        """Write data to a GCS file."""
        blob = self.bucket.blob(relative_path)
        blob.upload_from_string(data)

    def list(self, relative_dir: str) -> list[str]:
        """List files in the specified GCS directory."""
        blobs = self.client.list_blobs(self.bucket_name, prefix=relative_dir)
        return [blob.name for blob in blobs]

    def delete(self, relative_path: str):
        """Delete a file from GCS."""
        blob = self.bucket.blob(relative_path)
        if not blob.exists():
            raise FileNotFoundError(f"The file '{relative_path}' does not exist in the GCS bucket.")
        blob.delete()
