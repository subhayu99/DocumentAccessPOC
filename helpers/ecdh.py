"""
This module provides a class for Elliptic-curve Diffie-Hellman (ECDH) key exchange operations, including key pair generation,
serialization/deserialization of keys, shared secret generation, and data encryption/decryption.
"""

from enum import IntEnum
from typing import Literal, NamedTuple, TypeVar, overload

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from helpers.aes import AESHelper


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
    private_key: ec.EllipticCurvePrivateKey
    public_key: ec.EllipticCurvePublicKey


# Define TypeVars for the key pair formats and str, bytes
TKeyPair = TypeVar("TKeyPair", KeyPairObjects, KeyPairBytes, KeyPairStrings)
StrBytes = TypeVar("StrBytes", str, bytes)


class ECDHHelper:
    """
    Helper class for ECDH key exchange operations, including key pair generation,
    serialization/deserialization of keys, shared secret generation, and data encryption/decryption.
    """

    @staticmethod
    @overload
    def generate_key_pair(
        out_format: Literal[KeyFormat.OBJECT, 0],
    ) -> KeyPairObjects: ...

    @staticmethod
    @overload
    def generate_key_pair(out_format: Literal[KeyFormat.BYTE, 1]) -> KeyPairBytes: ...

    @staticmethod
    @overload
    def generate_key_pair(
        out_format: Literal[KeyFormat.STRING, 2],
    ) -> KeyPairStrings: ...

    @staticmethod
    def generate_key_pair(out_format: KeyFormat | int = KeyFormat.OBJECT) -> TKeyPair:
        """
        Generates an elliptic curve key pair in the specified format.

        :param out_format: Desired output format for the key pair (OBJECT, BYTE, STRING).
        :return: Key pair in the specified format.
        """
        if out_format not in [KeyFormat.BYTE, KeyFormat.STRING, KeyFormat.OBJECT]:
            out_format = KeyFormat.OBJECT

        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()

        if out_format == KeyFormat.BYTE:
            return KeyPairStrings(
                ECDHHelper.serialize_private_key(private_key, return_type=bytes),
                ECDHHelper.serialize_public_key(public_key, return_type=bytes),
            )
        elif out_format == KeyFormat.STRING:
            return KeyPairBytes(
                ECDHHelper.serialize_private_key(private_key, return_type=str),
                ECDHHelper.serialize_public_key(public_key, return_type=str),
            )
        elif out_format == KeyFormat.OBJECT:
            return KeyPairObjects(private_key, public_key)

    @staticmethod
    def serialize_private_key(
        private_key: ec.EllipticCurvePrivateKey, return_type: type[StrBytes] = bytes
    ) -> StrBytes:
        """
        Serializes a private key to PEM format.

        :param private_key: Elliptic curve private key.
        :param as_string: Whether to return the serialized key as a string or bytes.
        :return: Serialized private key in PEM format.
        """
        key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return key.decode() if return_type is str else key

    @staticmethod
    def deserialize_private_key(data: bytes | str):
        """
        Deserializes a PEM-encoded private key from bytes or hex string.

        :param data: Serialized private key in bytes or hex string format.
        :return: Elliptic curve private key object.
        """
        if isinstance(data, str):
            data = bytes.fromhex(data)
        return serialization.load_pem_private_key(
            data, password=None, backend=default_backend()
        )

    @staticmethod
    def serialize_public_key(
        public_key: ec.EllipticCurvePublicKey, return_type: type[StrBytes] = bytes
    ) -> StrBytes:
        """
        Serializes a public key to PEM format.

        :param public_key: Elliptic curve public key.
        :param as_string: Whether to return the serialized key as a string or bytes.
        :return: Serialized public key in PEM format.
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
        :return: Elliptic curve public key object.
        """
        if isinstance(data, str):
            data = bytes.fromhex(data)
        return serialization.load_pem_public_key(data, backend=default_backend())

    @staticmethod
    def generate_shared_secret(
        private_key: ec.EllipticCurvePrivateKey, public_key: ec.EllipticCurvePublicKey
    ):
        """
        Generates a shared secret using ECDH key exchange.

        :param private_key: Elliptic curve private key.
        :param public_key: Elliptic curve public key.
        :return: Shared secret bytes.
        """
        shared_secret = private_key.exchange(ec.ECDH(), public_key)
        return shared_secret

    @staticmethod
    def encrypt_data(data: bytes, shared_secret: bytes):
        """
        Encrypts data using AES encryption with the given shared secret.

        :param data: Data to encrypt.
        :param shared_secret: Shared secret used for encryption.
        :return: Encrypted data (ciphertext).
        """
        ciphertext = AESHelper(shared_secret).encrypt(data)
        return ciphertext

    @staticmethod
    def decrypt_data(ciphertext: bytes, shared_secret: bytes):
        """
        Decrypts data using AES encryption with the given shared secret.

        :param ciphertext: Encrypted data (ciphertext).
        :param shared_secret: Shared secret used for decryption.
        :return: Decrypted data.
        """
        data = AESHelper(shared_secret).decrypt(ciphertext)
        return data
