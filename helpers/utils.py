import re
import uuid
import hashlib
from io import BytesIO
from pathlib import Path
from typing import TypeVar


StrUuid = TypeVar("StrUuid", str, uuid.UUID)


def slugify(
    text: str, replace_specials_with: str = "_", replace_spaces_with: str = "-"
) -> str:
    """
    Convert a given string into a slug format.

    Args:
        text (str): The string to be converted into a slug.
        replace_specials_with (str, optional): The character to replace special characters with. Defaults to "_.
        replace_spaces_with (str, optional): The character to replace spaces with. Defaults to "-".

    Returns:
        str: The slugified string.
    """
    return (
        re.sub(r"[^\w\s-]+", replace_specials_with, text)
        .strip()
        .lower()
        .replace(" ", replace_spaces_with)
    )


def hash_text(text: str, base_uuid: uuid.UUID | None = None):
    """
    Generates a hash-based UUID using the given text and an optional base UUID.

    Args:
        text (str): The text to be used for generating the hash-based UUID.
        base_uuid (uuid.UUID | None, optional): The optional base UUID to use for hashing. Defaults to None.

    Returns:
        uuid.UUID: The hash-based UUID generated from the input text and base UUID.
    """
    if not isinstance(base_uuid, uuid.UUID):
        base_uuid = uuid.NAMESPACE_DNS
    return uuid.uuid3(base_uuid, text)


def hash_file(
    file: str | Path | bytes, algorithm="sha256", return_type: type[StrUuid] = uuid.UUID
) -> StrUuid:
    """
    Calculate the hash of a file or its contents.

    Args:
        file (str  | Path | bytes): Path to the file or contents of the file as bytes.
        algorithm (str): Hashing algorithm (default is 'sha256').
                         Options include 'md5', 'sha1', 'sha256', 'sha512', etc.
        return_type (type[str | uuid.UUID]): Type to return the hash as (default is uuid.UUID).

    Returns:
        str | uuid.UUID: The hash of the file or its contents as a string or UUID.
    """
    hash_func = hashlib.new(algorithm)
    buffer_size = 65536  # Read in chunks of 64 KB

    if isinstance(file, (str, Path)):
        if not Path(file).exists():
            raise FileNotFoundError(
                f"The file '{file}' does not exist in the local file system."
            )
        file_reader = open(file, "rb")
    else:
        file_reader = BytesIO(file)

    try:
        while chunk := file_reader.read(buffer_size):
            hash_func.update(chunk)
        _hash = hash_func.hexdigest()
        if return_type == uuid.UUID:
            return hash_text(_hash)
        return _hash
    finally:
        file_reader.close()


def hash_bytes(
    data: bytes, algorithm="sha256", return_type: type[StrUuid] = uuid.UUID
) -> StrUuid:
    """
    Calculate the hash of the given bytes using the specified algorithm.

    Args:
        data (bytes): The data to be hashed.
        algorithm (str): Hashing algorithm to use (default is 'sha256').
                         Options include 'md5', 'sha1', 'sha256', 'sha512', etc.
        return_type (type[str | uuid.UUID]): Type to return the hash as (default is uuid.UUID).

    Returns:
        str | uuid.UUID: The hash of the data as a string or UUID.
    """

    return hash_file(data, algorithm, return_type)
