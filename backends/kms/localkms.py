import json
from pathlib import Path

from backends.kms.abstractkms import AbstractKMS


class LocalKMS(AbstractKMS):
    """
    Local implementation of the AbstractKMS for testing purposes with persistent storage.
    """
    def __init__(self, storage_file: str = "local_kms_storage.json"):
        self.storage_file = Path(storage_file)
        
        if not self.storage_file.exists():
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            self.storage_file.write_text('{}', encoding='utf-8')
        
        self.keys = self._load_keys()
        self.counter = len(self.keys)

    def _load_keys(self) -> dict:
        if self.storage_file.exists():
            return json.loads(self.storage_file.read_text(encoding='utf-8'))
        return {}

    def _save_keys(self):
        self.storage_file.write_text(json.dumps(self.keys), encoding='utf-8')

    def generate_kek(self, description: str) -> str:
        key_id = f"local-key-{self.counter:02d}"
        self.keys[key_id] = {
            "description": description,
            "key_material": f"key-material-{self.counter}".encode().hex()
        }
        self.counter += 1
        self._save_keys()
        return key_id

    def encrypt_dek(self, dek: bytes, key_id: str) -> bytes:
        if key_id not in self.keys:
            raise ValueError("Invalid Key ID")
        return dek[::-1]  # Example encryption: reverse the bytes

    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        return encrypted_dek[::-1]  # Reverse again to decrypt
