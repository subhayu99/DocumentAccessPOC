import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, Session, select

from helpers.utils import hash_file, slugify
from models.user import User
from helpers.aes import AESHelper as AES
from helpers.rsa import RSAHelper as RSA
from config import DOCUMENT_STORE, getEngine
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

    Attributes:
        filepath (str): The filepath of the document.
        content (bytes): The content of the document in bytes.
    """
    content: bytes = Field(description="The content of the document in bytes")

class DocumentBase(DocumentDownloadResponse):
    """
    Base model for creating new documents.

    This model is used to create new documents in the system. It contains the
    essential information required to create a document, such as the filepath
    and content of the document.

    Attributes:
        filepath (str): The filepath of the document.
        content (bytes): The content of the document in bytes.
        give_access_to (list[str]): A list of User IDs to give access to this
            document. The users specified in this list will be able to access
            the document once it is uploaded.
    """
    give_access_to: list[str] = Field(
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

    Methods:
        `write_content(content: bytes):`
            Writes the provided encrypted content to the document's file path.

        `get_content() -> bytes:`
            Retrieves the encrypted content of the document from the document store.

        `update_shared_keys_registry(user_ids: list[str], dek: bytes):`
            Updates the shared keys registry for specified user IDs with the given DEK.

        `get_dek(user_id: str, user_private_key: bytes) -> bytes:`
            Retrieves and decrypts the DEK for a specified user using their private key.

        `from_base(document: DocumentBase) -> Document:`
            Creates a Document instance from a DocumentBase instance.

        `upload(document: DocumentBase) -> Document:`
            Uploads a new document to the system, managing its encryption and access.

        `share(user_ids: list[str], owner_private_key: bytes) -> Document:`
            Shares the document with specified users.

        `download(user_id: str, user_private_key: bytes) -> DocumentDownloadResponse:`
            Downloads the document content for a specified user.

        `delete():`
            Deletes the document from the document store and the database.

        `users_with_access -> list[str]:`
            Retrieves the list of user IDs with access to this document.

        `get_shared_documents(user_id: str) -> list[Document]:`
            Retrieves the list of documents shared with the given user.
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    hash: str
    uploaded_on: datetime = Field(default_factory=datetime.now)
    shared_keys: list[SharedKeyRegistry] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"primaryjoin": "SharedKeyRegistry.document_id == Document.id"},
        cascade_delete=True,
    )
    
    @property
    def local_path(self) -> str:
        return f"{slugify(self.owner_id)}-{self.filepath}"

    def write_content(self, content: bytes):
        DOCUMENT_STORE.write(self.local_path, content)

    def get_content(self):
        return DOCUMENT_STORE.read(self.local_path)

    def update_shared_keys_registry(self, user_ids: list[str], dek: bytes):
        user_id_obj_map = User.get_id_obj_map(user_ids)
        for user_id, user in user_id_obj_map.items():
            shared_key = SharedKeyRegistry(
                user_id=user_id,
                document_id=str(self.id),
                shared_key=RSA.encrypt_data(dek, user.public_key),
            )
            shared_key.upsert()

    def get_dek(self, user_id: str, user_private_key: bytes):
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

    @classmethod
    def upload(cls, document: DocumentBase):
        owner_id = document.owner_id
        if User.get_by_id(owner_id) is None:
            raise ValueError(f"User ({owner_id}) not found")

        dek = AES.get_random_key()
        encrypted_content = AES(dek).encrypt(document.content)
        doc = Document(
            filepath=document.filepath,
            owner_id=owner_id,
            hash=hash_file(document.content, as_uuid=False),
        ).create()
        doc.update_shared_keys_registry([owner_id, *document.give_access_to], dek)
        doc.write_content(encrypted_content)
        return doc

    def share(self, user_ids: list[str], owner_private_key: bytes) -> "Document":
        dek = self.get_dek(self.owner_id, owner_private_key)
        self.update_shared_keys_registry(user_ids, dek)
        return self

    def download(self, user_id: str, user_private_key: bytes):
        dek = self.get_dek(user_id, user_private_key)
        content = self.get_content()
        return DocumentDownloadResponse(
            filepath=self.filepath,
            content=AES(dek).decrypt(content),
            owner_id=self.owner_id,
        )

    def delete(self):
        DOCUMENT_STORE.delete(self.filepath)
        super().delete()

    @property
    def users_with_access(self):
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