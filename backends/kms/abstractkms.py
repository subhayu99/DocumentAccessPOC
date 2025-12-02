from abc import ABC, abstractmethod


class AbstractKMS(ABC):
    """
    Abstract base class for Key Management System operations.
    """

    @abstractmethod
    def generate_kek(self, description: str) -> str:
        """
        Generate a Key Encryption Key (KEK).

        Args:
            description (str): Description for the key.
        Returns:
            str: Key ID of the generated KEK.
        """
        pass

    @abstractmethod
    def encrypt_dek(self, dek: bytes, key_id: str) -> bytes:
        """
        Encrypt a Data Encryption Key (DEK).

        Args:
            dek (bytes): The plaintext DEK to encrypt.
            key_id (str): The Key ID to use for encryption.
        Returns:
            bytes: Encrypted DEK as bytes.
        """
        pass

    @abstractmethod
    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        """
        Decrypt a Data Encryption Key (DEK).

        Args:
            encrypted_dek (bytes): The encrypted DEK to decrypt.
        Returns:
            bytes: Plaintext DEK as bytes.
        """
        pass
