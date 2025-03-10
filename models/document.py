import uuid
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, Session, select

from models.user import User
from helpers.aes import AESHelper as AES
from helpers.rsa import RSAHelper as RSA
from config import DOCUMENT_STORE, getEngine
from helpers.utils import hash_file, hash_text
from models.base import SQLModel, SQLModelWithID


class SharedKeyRegistry(SQLModel, table=True):
    """
    Stores the shared encryption keys for a given document and user pair.

    The shared key is encrypted using the user's public key, and can be decrypted
    by the user using their private key. This allows the user to access the document
    without having to be re-shared the document.

    The shared key is stored in the database as a binary blob, and is encrypted
    using the user's public key. This means that only the user who the document is
    shared with can decrypt the shared key.

    Attributes:
        user_id (str): The User ID of the user the document is shared with.
        document_id (str): The Document ID of the document that is shared.
        shared_key (bytes): The encrypted shared key.
        created_at (datetime): The timestamp when the shared key was created.
        document (Document): The document that is shared.
        user (User): The user that the document is shared with.
    """
    user_id: str = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")
    document_id: str = Field(foreign_key="document.id", primary_key=True, ondelete="CASCADE")
    shared_key: bytes
    created_at: datetime = Field(default_factory=datetime.now)
    document: "Document" = Relationship(back_populates="shared_keys")
    user: "User" = Relationship(back_populates="shared_keys")


class DocumentCommon(SQLModel):
    """
    Common fields for Document and DocumentBase models.

    This class serves as a base for storing common attributes related to documents. 
    It provides a standardized way to define the essential properties required for 
    handling documents within the system. The attributes defined here are shared 
    among different document models to ensure consistency.

    Attributes:
        filepath (str): The filepath of the document. This is used to locate the 
            document in the storage system. The path is indexed to improve the 
            performance of queries that filter or sort based on the document's path.
        
        owner_id (str): The User ID of the owner of the document. This field 
            establishes an ownership link between the document and a user in the 
            system. It uses a foreign key reference to ensure that the owner_id 
            corresponds to a valid user in the database.
    """
    filepath: str = Field(index=True, description="The filepath of the document")
    owner_id: str = Field(
        foreign_key="user.id", description="User ID of the Owner of the document"
    )


class DocumentDownloadResponse(DocumentCommon):
    """
    Document download response model.

    This model is used to represent a document that is being downloaded from the
    server. It contains the filepath and content of the document.
    """
    content: bytes = Field(description="The content of the document in bytes")

class DocumentShareResponse(DocumentCommon):
    """
    Document share response model.

    This model is used to represent a document that is being shared with another
    user.
    """
    id: str
    owner_id: str
    uploaded_on: datetime
    shared_with: list[str] = Field(default_factory=list)
    not_shared_with: list[str] = Field(default_factory=list)

class DocumentBase(DocumentDownloadResponse):
    """
    Base model for creating new documents.

    This model is used to create new documents in the system. It contains the
    essential information required to create a document, such as the filepath
    and content of the document.
    """
    share_with: list[str] = Field(
        default_factory=list, description="User IDs to give access to this document."
    )

class Document(SQLModelWithID, DocumentCommon, table=True):
    """
    A document is a file that can be accessed by the users of the system. Each
    document has a unique ID, filepath, content, and owner. The owner is the
    user who originally uploaded the document.

    The document is stored in the file system, and the filepath is used to
    identify the document. The content of the document is encrypted using the
    Data Encryption Key (DEK) before it is stored in the file system.

    Each document has a list of users who have access to the document. The
    access is granted using the User ID of the users. The users with access
    to the document can download the document.

    Attributes:
        id (str): Unique identifier for the document.
        filepath (str): The filepath of the document in the file system.
        content (bytes): The content of the document in bytes.
        owner_id (str): The User ID of the owner of the document.
        shared_keys (list[SharedKeyRegistry]): A list of SharedKeyRegistry
            objects that store the shared encryption keys for the document.
        uploaded_on (datetime): The timestamp when the document was uploaded.
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    hash: str
    uploaded_on: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    shared_keys: list[SharedKeyRegistry] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"primaryjoin": "SharedKeyRegistry.document_id == Document.id"},
        cascade_delete=True,
    )
    
    @property
    def local_path(self) -> str:
        return f"{self.id}.bin"

    def write_content(self, content: bytes):
        DOCUMENT_STORE.write(self.local_path, content)

    def get_content(self):
        return DOCUMENT_STORE.read(self.local_path)

    def update_shared_keys_registry(self, user_ids: list[str], dek: bytes):
        """
        Updates the shared keys registry for the given users.

        This function updates the SharedKeyRegistry table with the given user
        IDs and the Data Encryption Key (DEK) for the document. The DEK is
        encrypted using the public key of each user and stored in the
        SharedKeyRegistry table.

        Args:
            user_ids (list[str]): A list of User IDs to update the shared
                keys registry for.
            dek (bytes): The Data Encryption Key (DEK) to store in the
                SharedKeyRegistry table. The DEK is encrypted using the
                public key of each user before it is stored.
        """
        user_id_obj_map = User.get_id_obj_map(user_ids)
        for user_id, user in user_id_obj_map.items():
            shared_key = SharedKeyRegistry(
                user_id=user_id,
                document_id=str(self.id),
                shared_key=RSA.encrypt_data(dek, user.public_key),
            )
            shared_key.upsert()

    def get_dek(self, user_id: str, user_private_key: bytes):
        """
        Get the DEK for the given user_id, using the private key provided.

        Args:
            user_id (str): The ID of the user.
            user_private_key (bytes): The user's private key.

        Returns:
            bytes: The DEK for the document.

        Raises:
            ValueError: If the document is not shared with the user or if the
                private key is invalid.
        """
        with Session(getEngine()) as db:
            rows = db.exec(
                select(SharedKeyRegistry)
                .where(
                    SharedKeyRegistry.document_id == self.id,
                    SharedKeyRegistry.user_id == user_id,
                )
            ).all()
        if len(rows) == 0:
            raise ValueError(f"Document({self.id}) not shared with User({user_id})")
        try:
            return RSA.decrypt_data(rows[-1].shared_key, user_private_key)
        except Exception:
            raise ValueError(f"Invalid private key for User({user_id})")

    @classmethod
    def from_base(cls, document: DocumentBase):
        return cls.upload(document)
    
    def _to_share_response(self, user_ids: list[str]):
        return DocumentShareResponse(
            id=self.id,
            filepath=self.filepath,
            owner_id=self.owner_id,
            uploaded_on=self.uploaded_on,
            shared_with=self.shared_with,
            not_shared_with=list(set(user_ids) - set(self.shared_with)),
        )

    @classmethod
    def upload(cls, document: DocumentBase):
        owner_id = document.owner_id
        if User.get_by_id(owner_id) is None:
            raise ValueError(f"User ({owner_id}) not found")

        file_hash = hash_file(document.content, return_type=str)
        doc_id = hash_text(f"{owner_id}-{document.filepath}-{file_hash}").hex
        
        # Check if document already exists (maybe use hash and/or filepath)
        record = Document.get_by_id(doc_id)
        if record is not None:
            return record._to_share_response(document.share_with)

        dek = AES.get_random_key()
        encrypted_content = AES(dek).encrypt(document.content)
        doc = Document(
            id=hash_text(f"{owner_id}-{document.filepath}-{file_hash}").hex,
            filepath=document.filepath,
            owner_id=owner_id,
            hash=file_hash,
        ).create()
        doc.update_shared_keys_registry([owner_id, *document.share_with], dek)
        doc.write_content(encrypted_content)
        return doc._to_share_response(document.share_with)

    def share(self, user_ids: list[str], owner_private_key: bytes) -> DocumentShareResponse:
        dek = self.get_dek(self.owner_id, owner_private_key)
        self.update_shared_keys_registry(user_ids, dek)
        return self._to_share_response(user_ids)
    
    def revoke_access(self, user_ids: list[str], owner_private_key: bytes) -> DocumentShareResponse:
        # This checks if the user is the owner
        dek = self.get_dek(self.owner_id, owner_private_key)  # noqa: F841
        
        if self.owner_id in user_ids:
            raise ValueError("Cannot revoke access to the owner")
        with Session(getEngine()) as db:
            rows = db.exec(
                select(SharedKeyRegistry)
                .where(
                    SharedKeyRegistry.document_id == self.id,
                    SharedKeyRegistry.user_id.in_(user_ids),
                )
            ).all()
        for row in rows:
            SharedKeyRegistry.delete(row)
        
        return self._to_share_response(user_ids)

    def download(self, user_id: str, user_private_key: bytes):
        dek = self.get_dek(user_id, user_private_key)
        content = self.get_content()
        return DocumentDownloadResponse(
            filepath=self.filepath,
            content=AES(dek).decrypt(content),
            owner_id=self.owner_id,
        )

    def delete(self):
        # Delete the document from the document store
        DOCUMENT_STORE.delete(self.filepath)
        
        # Delete the shared keys
        with Session(getEngine()) as db:
            rows = db.exec(
                select(SharedKeyRegistry)
                .where(
                    SharedKeyRegistry.document_id == self.id,
                )
            ).all()
            for row in rows:
                SharedKeyRegistry.delete(row)
        
        # Delete the document itself
        super().delete()

    @property
    def shared_with(self):
        with Session(getEngine()) as db:
            rows = db.exec(
                select(SharedKeyRegistry)
                .where(
                    SharedKeyRegistry.document_id == self.id,
                )
            ).all()
        return [row.user_id for row in rows]

    @classmethod
    def get_shared_documents(cls, user_id: str):
        with Session(getEngine()) as db:
            rows = db.exec(
                select(SharedKeyRegistry)
                .where(
                    SharedKeyRegistry.user_id == user_id,
                )
            ).all()
        return list(cls.get_by_ids([row.document_id for row in rows]))
