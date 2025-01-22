import boto3

from backends.kms.abstractkms import AbstractKMS


class AWSKMS(AbstractKMS):
    """
    AWS KMS implementation of the AbstractKMS.
    """

    def __init__(self):
        self.kms_client = boto3.client('kms')

    def generate_kek(self, description: str) -> str:
        response = self.kms_client.create_key(
            Description=description,
            KeyUsage='ENCRYPT_DECRYPT',
            CustomerMasterKeySpec='SYMMETRIC_DEFAULT'
        )
        return response['KeyMetadata']['KeyId']

    def encrypt_dek(self, dek: bytes, key_id: str) -> bytes:
        response = self.kms_client.encrypt(
            KeyId=key_id,
            Plaintext=dek
        )
        return response['CiphertextBlob']

    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        response = self.kms_client.decrypt(
            CiphertextBlob=encrypted_dek
        )
        return response['Plaintext']
