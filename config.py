from sqlmodel import create_engine

from backends.filesystem.localfs import LocalFileSystem


DATA_STORE = LocalFileSystem("./data")
DOCUMENT_STORE = LocalFileSystem("./data/documents")

JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

DATABASE_URL = "sqlite:///" + (DATA_STORE.root / "db.sqlite").as_posix()

def getEngine():
    return create_engine(
        DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
    )
