from typing import Dict, List, Optional
from dataclasses import dataclass, field

from infisical_sdk.api_types import BaseModel
from infisical_sdk import InfisicalSDKClient as InfisicalClient


@dataclass
class BaseKey(BaseModel):
    createdAt: str
    id: str
    name: str
    orgId: str
    updatedAt: str
    description: Optional[str] = None
    isDisabled: Optional[bool] = field(default=False)
    isReserved: Optional[bool] = field(default=True)
    projectId: Optional[str] = None
    slug: Optional[str] = None


@dataclass
class ListKey(BaseKey):
    encryptionAlgorithm: str = "aes-256-gcm"
    version: int = 1

@dataclass
class ListKeysResponse(BaseModel):
    keys: List[ListKey]
    totalCount: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'ListKeysResponse':
        return cls(
            keys=[ListKey.from_dict(key) for key in data['keys']],
            totalCount=data['totalCount']
        )


@dataclass
class SingleKeyResponse(BaseModel):
    key: BaseKey

    @classmethod
    def from_dict(cls, data: Dict) -> 'SingleKeyResponse':
        return cls(
            key=BaseKey.from_dict(data['key'])
        )

@dataclass
class EncryptDataResponse(BaseModel):
    ciphertext: str


@dataclass
class DecryptDataResponse(BaseModel):
    plaintext: str


class V1Keys:
    def __init__(self, client: InfisicalClient):
        """
        Initializes the KeysAPI class.

        Args:
            client: An instance of the API client.
        """
        self.client = client

    def list_keys(
        self,
        project_id: str,
        offset: int = 0,
        limit: int = 100,
        order_by: str = "name",
        order_direction: str = "asc",
        search: str = None,
    ) -> ListKeysResponse:
        """
        List KMS keys for a given project.

        Args:
            project_id: The project ID to list keys from.
            offset: The offset to start from.
            limit: The number of keys to return.
            order_by: The column to order keys by.
            order_direction: The direction to order keys (asc/desc).
            search: A text string to filter key names.

        Returns:
            A dictionary containing the list of keys and the total count.
        """
        params = {
            "projectId": project_id,
            "offset": offset,
            "limit": limit,
            "orderBy": order_by,
            "orderDirection": order_direction,
        }
        if search:
            params["search"] = search

        response = self.client.api.get(
            path="/api/v1/kms/keys", model=ListKeysResponse, params=params
        )
        return response.data

    def create_key(
        self,
        name: str,
        project_id: str,
        description: str = None,
        encryption_algorithm: str = "aes-256-gcm",
    ) -> BaseKey:
        """
        Create a new KMS key.

        Args:
            name: The name of the key.
            project_id: The project ID to create the key in.
            description: An optional description of the key.
            encryption_algorithm: The encryption algorithm to use.

        Returns:
            A dictionary containing the created key details.
        """
        body = {
            "name": name,
            "projectId": project_id,
            "description": description,
            "encryptionAlgorithm": encryption_algorithm,
        }
        response = self.client.api.post(
            path="/api/v1/kms/keys", model=SingleKeyResponse, json=body
        )
        return response.data.key

    def update_key(
        self,
        key_id: str,
        name: str = None,
        description: str = None,
        is_disabled: bool = None,
    ) -> BaseKey:
        """
        Update a KMS key.

        Args:
            key_id: The ID of the key to update.
            name: The updated name of the key.
            description: The updated description of the key.
            is_disabled: Flag to enable or disable the key.

        Returns:
            A dictionary containing the updated key details.
        """
        body = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        if is_disabled is not None:
            body["isDisabled"] = is_disabled

        response = self.client.api.patch(
            path=f"/api/v1/kms/keys/{key_id}", model=SingleKeyResponse, json=body
        )
        return response.data.key

    def delete_key(self, key_id: str) -> BaseKey:
        """
        Delete a KMS key.

        Args:
            key_id: The ID of the key to delete.

        Returns:
            A dictionary containing the details of the deleted key.
        """
        response = self.client.api.delete(
            path=f"/api/v1/kms/keys/{key_id}", model=SingleKeyResponse
        )
        return response.data.key

    def encrypt_data(self, key_id: str, plaintext: str) -> EncryptDataResponse:
        """
        Encrypt data using a KMS key.

        Args:
            key_id: The ID of the key to encrypt the data with.
            plaintext: The plaintext to be encrypted (base64 encoded).

        Returns:
            A dictionary containing the ciphertext.
        """
        body = {"plaintext": plaintext}
        response = self.client.api.post(
            path=f"/api/v1/kms/keys/{key_id}/encrypt",
            model=EncryptDataResponse,
            json=body,
        )
        return response.data

    def decrypt_data(self, key_id: str, ciphertext: str) -> DecryptDataResponse:
        """
        Decrypt data using a KMS key.

        Args:
            key_id: The ID of the key to decrypt the data with.
            ciphertext: The ciphertext to be decrypted (base64 encoded).

        Returns:
            A dictionary containing the plaintext.
        """
        body = {"ciphertext": ciphertext}
        response = self.client.api.post(
            path=f"/api/v1/kms/keys/{key_id}/decrypt",
            model=DecryptDataResponse,
            json=body,
        )
        return response.data


class InfisicalSDKClient(InfisicalClient):
    def __init__(self, host: str, token: str = None):
        super().__init__(host, token)
        self.keys = V1Keys(self)
