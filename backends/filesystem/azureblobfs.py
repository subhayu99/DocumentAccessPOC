from azure.storage.blob import BlobServiceClient
from backends.filesystem.abstractfs import AbstractFileSystem


class AzureBlobFileSystem(AbstractFileSystem):
    """Azure Blob Storage implementation of the FileSystemInterface."""

    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = self.client.get_container_client(container_name)

    def read(self, relative_path: str) -> bytes:
        """Read data from an Azure Blob."""
        blob_client = self.container.get_blob_client(relative_path)
        if not blob_client.exists():
            raise FileNotFoundError(f"The file '{relative_path}' does not exist in the Azure container.")
        return blob_client.download_blob().readall()

    def write(self, relative_path: str, data: bytes):
        """Write data to an Azure Blob."""
        blob_client = self.container.get_blob_client(relative_path)
        blob_client.upload_blob(data, overwrite=True)

    def list(self, relative_dir: str) -> list[str]:
        """List files in the specified Azure Blob directory."""
        blobs = self.container.list_blobs(name_starts_with=relative_dir)
        return [blob.name for blob in blobs]

    def delete(self, relative_path: str):
        """Delete a file from Azure Blob Storage."""
        blob_client = self.container.get_blob_client(relative_path)
        if not blob_client.exists():
            raise FileNotFoundError(f"The file '{relative_path}' does not exist in the Azure container.")
        blob_client.delete_blob()
