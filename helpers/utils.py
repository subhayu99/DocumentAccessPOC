import re
import uuid
import hashlib
from pathlib import Path
from io import BytesIO


def slugify(text: str, replace_specials_with: str = "_", replace_spaces_with: str = "-") -> str:
    return re.sub(r'[^\w\s-]+', replace_specials_with, text).strip().lower().replace(' ', replace_spaces_with)

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


def hash_file(file: str | Path | bytes, algorithm='sha256', as_uuid=True):
    """
    Calculate the hash of a file or its contents.

    Args:
        file (str  | Path | bytes): Path to the file or contents of the file as bytes.
        algorithm (str): Hashing algorithm (default is 'sha256').
                         Options include 'md5', 'sha1', 'sha256', 'sha512', etc.
        as_uuid (bool): Whether to return the hash as a UUID (default is True).
                         If True, the hash will be converted to a UUID. Else, the hash will be returned as a string.

    Returns:
        str | uuid.UUID: The hash of the file or its contents as a string or UUID.
    """
    hash_func = hashlib.new(algorithm)
    buffer_size = 65536  # Read in chunks of 64 KB

    if isinstance(file, (str, Path)):
        if not Path(file).exists():
            raise FileNotFoundError(f"The file '{file}' does not exist in the local file system.")
        file_reader = open(file, 'rb')
    else:
        file_reader = BytesIO(file)

    try:
        while chunk := file_reader.read(buffer_size):
            hash_func.update(chunk)
        _hash = hash_func.hexdigest()
        if as_uuid:
            return hash_text(_hash)
        return _hash
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        file_reader.close()

