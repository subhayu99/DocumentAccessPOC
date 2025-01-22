"""
This module provides a class for encrypting and decrypting data using AES in GCM mode.
"""

from typing import Literal

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from helpers.utils import hash_text


class AESHelper:
    def __init__(self, key: bytes | str):
        """
        Initialize the AESHelper instance with the provided key.
        Returns the hex-encoded AES key.
        Raises a TypeError if the key is not a string or bytes.
        """
        if not isinstance(key, (bytes, str)):
            raise TypeError("Key must be a string or bytes.")
        
        if isinstance(key, str):
            key = self.try_encode_str(key)
        
        if not isinstance(key, bytes):
            raise ValueError("Cannot convert key to bytes.")
        
        self.key = key
    
    @staticmethod
    def try_encode_str(key: str) -> bytes | None:
        if not isinstance(key, str):
            return key
        if len(key) not in [16, 24, 32]:
            key = hash_text(key).hex
        try:
            return bytes.fromhex(key)
        except Exception:
            pass
        try:
            return key.encode()
        except Exception:
            pass

    @staticmethod
    def get_random_key(size: Literal[16, 24, 32] = 16):
        """
        Generate a random AES key of the specified size (16, 24, or 32 bytes).
        Returns the key as a hex-encoded string.
        """
        return get_random_bytes(size)
    
    @staticmethod
    def _verify_data_type(data: bytes):
        """
        Verify that the provided data is of type bytes.
        Raises a TypeError if the data is not bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError("Data must be bytes.")

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using AES in GCM mode.
        Returns the ciphertext, which includes the nonce and authentication tag.
        """
        self._verify_data_type(data)
        cipher = AES.new(self.key, AES.MODE_GCM)  # GCM mode automatically generates a nonce
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data using AES in GCM mode.
        Extracts the nonce, tag, and ciphertext from the encrypted data.
        Returns the decrypted data.
        """
        self._verify_data_type(encrypted_data)
        nonce = encrypted_data[:16]  # GCM nonce is 16 bytes
        tag = encrypted_data[16:32]  # GCM tag is 16 bytes
        ciphertext = encrypted_data[32:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)


# Example usage:
if __name__ == "__main__":
    # Generate a new AES key
    key = AESHelper.get_random_key(16)
    print(f"Generated Key (hex): {key.hex()}")

    # Initialize the class with the generated key
    aes = AESHelper(key)

    # Data to encrypt
    data = b"Sensitive Data to Encrypt"

    # Encrypt the data
    encrypted_data = aes.encrypt(data)
    print(f"Encrypted Data (hex): {encrypted_data.hex()}")

    # Decrypt the data
    decrypted_data = aes.decrypt(encrypted_data)
    print(f"Decrypted Data: {decrypted_data.decode()}")
