from abc import ABC, abstractmethod


class AbstractKMS(ABC):
    """
    Abstract base class for Key Management System operations.
    """

    @abstractmethod
    def generate_kek(self, description: str) -> str:
        """
        Generate a Key Encryption Key (KEK).

        :param description: Description for the key.
        :return: Key ID of the generated KEK.
        """
        pass

    @abstractmethod
    def encrypt_dek(self, dek: bytes, key_id: str) -> bytes:
        """
        Encrypt a Data Encryption Key (DEK).

        :param dek: The plaintext DEK to encrypt.
        :param key_id: The Key ID to use for encryption.
        :return: Encrypted DEK as bytes.
        """
        pass

    @abstractmethod
    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        """
        Decrypt a Data Encryption Key (DEK).

        :param encrypted_dek: The encrypted DEK to decrypt.
        :return: Plaintext DEK as bytes.
        """
        pass
