"""
This module provides a class for RSA key exchange operations, including key pair generation,
serialization/deserialization of keys, and data encryption/decryption.
"""

from enum import IntEnum
from typing import NamedTuple, TypeVar, overload, Literal

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


class KeyFormat(IntEnum):
    OBJECT = 0
    BYTE = 1
    STRING = 2


class KeyPairStrings(NamedTuple):
    private_key: str
    public_key: str


class KeyPairBytes(NamedTuple):
    private_key: bytes
    public_key: bytes


class KeyPairObjects(NamedTuple):
    private_key: rsa.RSAPrivateKey
    public_key: rsa.RSAPublicKey


# Define TypeVars for the key pair formats and str, bytes
TKeyPair = TypeVar("TKeyPair", KeyPairObjects, KeyPairBytes, KeyPairStrings)
StrBytes = TypeVar("StrBytes", str, bytes)


class RSAHelper:
    """
    Helper class for RSA key exchange operations, including key pair generation,
    serialization/deserialization of keys, and data encryption/decryption.
    """

    @staticmethod
    @overload
    def generate_key_pair(out_format: Literal[KeyFormat.OBJECT, 0]) -> KeyPairObjects:
        ...

    @staticmethod
    @overload
    def generate_key_pair(out_format: Literal[KeyFormat.BYTE, 1]) -> KeyPairBytes:
        ...

    @staticmethod
    @overload
    def generate_key_pair(out_format: Literal[KeyFormat.STRING, 2]) -> KeyPairStrings:
        ...

    @staticmethod
    def generate_key_pair(out_format: KeyFormat | int = KeyFormat.OBJECT) -> TKeyPair:
        """
        Generates an RSA key pair in the specified format.

        :param out_format: Desired output format for the key pair (OBJECT, BYTE, STRING).
        :return: Key pair in the specified format.
        """
        if out_format not in [KeyFormat.BYTE, KeyFormat.STRING, KeyFormat.OBJECT]:
            out_format = KeyFormat.OBJECT

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()

        if out_format == KeyFormat.BYTE:
            return KeyPairBytes(
                RSAHelper.serialize_private_key(private_key, return_type=bytes),
                RSAHelper.serialize_public_key(public_key, return_type=bytes),
            )
        elif out_format == KeyFormat.STRING:
            return KeyPairStrings(
                RSAHelper.serialize_private_key(private_key, return_type=str),
                RSAHelper.serialize_public_key(public_key, return_type=str),
            )
        elif out_format == KeyFormat.OBJECT:
            return KeyPairObjects(private_key, public_key)

    @staticmethod
    def serialize_private_key(private_key: rsa.RSAPrivateKey, return_type: type[StrBytes] = bytes) -> StrBytes:
        """
        Serializes a private key to PEM format.

        :param private_key: RSA private key.
        :param return_type: Whether to return the serialized key as a string or bytes.
        :return: Serialized private key in PEM format.
        """
        key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return key.decode() if return_type is str else key

    @staticmethod
    def deserialize_private_key(data: bytes | str):
        """
        Deserializes a PEM-encoded private key from bytes or hex string.

        :param data: Serialized private key in bytes or hex string format.
        :return: RSA private key object.
        """
        if isinstance(data, str):
            data = data.encode()
        try:
            key = serialization.load_pem_private_key(
                data, password=None, backend=default_backend()
            )
            return key
        except Exception as e:
            raise ValueError(f"Failed to deserialize private key: {e}")

    @staticmethod
    def serialize_public_key(public_key: rsa.RSAPublicKey, return_type: type[StrBytes] = bytes) -> StrBytes:
        """
        Serializes a public key to PEM format.

        :param public_key: RSA public key.
        :param return_type: Desired return type for the serialized key (str or bytes).
        :return: Serialized public key in PEM format as a string or bytes.
        """
        key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return key.decode() if return_type is str else key

    @staticmethod
    def deserialize_public_key(data: bytes | str):
        """
        Deserializes a PEM-encoded public key from bytes or hex string.

        :param data: Serialized public key in bytes or hex string format.
        :return: RSA public key object.
        """
        if isinstance(data, str):
            data = data.encode()
        try:
            key = serialization.load_pem_public_key(data, backend=default_backend())
            return key
        except Exception as e:
            raise ValueError(f"Failed to deserialize public key: {e}")

    @staticmethod
    def get_padding():
        """
        Returns an OAEP padding object configured with MGF1 using SHA-256
        as the hash algorithm. This padding is used for RSA encryption
        to provide additional security measures, such as preventing
        chosen ciphertext attacks. No label is used in this configuration.
        """
        return padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),  # Mask generation function
            algorithm=hashes.SHA256(),  # Hash algorithm used for OAEP
            label=None,  # No label is used
        )

    @staticmethod
    def encrypt_data(data: bytes, public_key: rsa.RSAPublicKey | str | bytes) -> bytes:
        """
        Encrypts data using AES encryption with the given shared secret.

        :param data: Data to encrypt.
        :param public_key: Public key used for encryption.
        :return: Encrypted data (ciphertext).
        """
        if isinstance(public_key, (str, bytes)):
            public_key = RSAHelper.deserialize_public_key(public_key)
        ciphertext = public_key.encrypt(data, RSAHelper.get_padding())
        return ciphertext

    @staticmethod
    def decrypt_data(
        ciphertext: bytes, private_key: rsa.RSAPrivateKey | str | bytes
    ) -> bytes:
        """
        Decrypts data using AES encryption with the given shared secret.

        :param ciphertext: Encrypted data (ciphertext).
        :param private_key: Private key used for decryption.
        :return: Decrypted data.
        """
        if isinstance(private_key, (str, bytes)):
            private_key = RSAHelper.deserialize_private_key(private_key)
        data = private_key.decrypt(ciphertext, RSAHelper.get_padding())
        return data

    @staticmethod
    def sign_data(data: bytes, private_key: rsa.RSAPrivateKey | str | bytes) -> bytes:
        """
        Signs the given data using the provided private key.

        :param data: Data to be signed.
        :param private_key: Private key used for signing, can be an RSAPrivateKey object, a PEM string, or bytes.
        :return: The generated signature as bytes.
        """
        if isinstance(private_key, (str, bytes)):
            private_key = RSAHelper.deserialize_private_key(private_key)
        signature = private_key.sign(data, RSAHelper.get_padding(), hashes.SHA256())
        return signature

    @staticmethod
    def verify_signature(
        data: bytes, signature: bytes, public_key: rsa.RSAPublicKey | str | bytes
    ) -> bool:
        """
        Verifies the given signature against the given data and public key.

        :param data: Data that was signed.
        :param signature: Signature to verify.
        :param public_key: Public key to use for verification, can be an RSAPublicKey object, a PEM string, or bytes.
        :return: True if the signature is valid, False otherwise.
        """
        if isinstance(public_key, (str, bytes)):
            public_key = RSAHelper.deserialize_public_key(public_key)
        try:
            public_key.verify(signature, data, RSAHelper.get_padding(), hashes.SHA256())
            return True
        except Exception:
            return False

    @staticmethod
    def verify_key_pair(
        private_key: rsa.RSAPrivateKey | str | bytes,
        public_key: rsa.RSAPublicKey | str | bytes,
    ) -> bool:
        """
        Verifies that the given private and public key are a matching pair.

        :param private_key: Private key to verify, can be an RSAPrivateKey object, a PEM string, or bytes.
        :param public_key: Public key to verify, can be an RSAPublicKey object, a PEM string, or bytes.
        :return: True if the key pair is valid, False otherwise.
        """
        if isinstance(private_key, (str, bytes)):
            private_key = RSAHelper.deserialize_private_key(private_key)
        if isinstance(public_key, (str, bytes)):
            public_key = RSAHelper.deserialize_public_key(public_key)
        return private_key.public_key() == public_key
