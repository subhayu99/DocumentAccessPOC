import pysftp
from ftplib import FTP

from backends.filesystem.abstractfs import AbstractFileSystem


class FTPFileSystem(AbstractFileSystem):
    """FTP implementation of the FileSystemInterface."""

    def __init__(self, host: str, username: str, password: str, port: int = 21):
        self.ftp = FTP()
        self.ftp.connect(host, port)
        self.ftp.login(username, password)

    def read(self, relative_path: str) -> bytes:
        """Read data from an FTP file."""
        with open('tempfile', 'wb') as temp_file:
            self.ftp.retrbinary(f"RETR {relative_path}", temp_file.write)
        with open('tempfile', 'rb') as temp_file:
            return temp_file.read()

    def write(self, relative_path: str, data: bytes):
        """Write data to an FTP file."""
        with open('tempfile', 'wb') as temp_file:
            temp_file.write(data)
        with open('tempfile', 'rb') as temp_file:
            self.ftp.storbinary(f"STOR {relative_path}", temp_file)

    def list(self, relative_dir: str) -> list[str]:
        """List files in the specified FTP directory."""
        return self.ftp.nlst(relative_dir)

    def delete(self, relative_path: str):
        """Delete a file from FTP."""
        self.ftp.delete(relative_path)


class SFTPFileSystem(AbstractFileSystem):
    """SFTP implementation of the FileSystemInterface."""

    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None  # Disable host key verification (optional, for testing only)
        self.connection = pysftp.Connection(
            host=host, username=username, password=password, port=port, cnopts=self.cnopts
        )

    def read(self, relative_path: str) -> bytes:
        """Read data from an SFTP file."""
        with self.connection.open(relative_path, 'rb') as file:
            return file.read()

    def write(self, relative_path: str, data: bytes):
        """Write data to an SFTP file."""
        with self.connection.open(relative_path, 'wb') as file:
            file.write(data)

    def list(self, relative_dir: str) -> list[str]:
        """List files in the specified SFTP directory."""
        return self.connection.listdir(relative_dir)

    def delete(self, relative_path: str):
        """Delete a file from SFTP."""
        self.connection.remove(relative_path)
