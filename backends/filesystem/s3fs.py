import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from backends.filesystem.abstract_fs import AbstractFileSystem


class S3FileSystem(AbstractFileSystem):
    """S3 file system implementation of the FileSystemInterface."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3 = boto3.client("s3", region_name=region)

    def read(self, relative_path: str):
        """Read data from the S3 file."""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=relative_path)
            return response["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            raise FileNotFoundError(
                f"The file '{relative_path}' does not exist in the S3 bucket."
            )
        except (NoCredentialsError, PartialCredentialsError):
            raise PermissionError("AWS credentials are missing or incomplete.")

    def write(self, relative_path: str, data: bytes):
        """Write data to an S3 file."""
        try:
            self.s3.put_object(Bucket=self.bucket_name, Key=relative_path, Body=data)
        except (NoCredentialsError, PartialCredentialsError):
            raise PermissionError("AWS credentials are missing or incomplete.")

    def list(self, relative_dir: str):
        """List files in the specified S3 bucket."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix=relative_dir
            )
            if "Contents" in response:
                return [item["Key"] for item in response["Contents"]]
            return []
        except (NoCredentialsError, PartialCredentialsError):
            raise PermissionError("AWS credentials are missing or incomplete.")

    def delete(self, relative_path: str):
        """Delete the file."""
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=relative_path)
        except self.s3.exceptions.NoSuchKey:
            raise FileNotFoundError(
                f"The file '{relative_path}' does not exist in the S3 bucket."
            )
        except (NoCredentialsError, PartialCredentialsError):
            raise PermissionError("AWS credentials are missing or incomplete.")
