"""
Module for configuring the application's storage backends, JWT settings, and database connection.

This module defines:
- Configurable file storage backends (`DATA_STORE` and `DOCUMENT_STORE`) that can be set to any backend
  supported by `backends.filesystem` (e.g., LocalFileSystem, S3).
- JWT-related constants, such as the secret key, algorithm, and token expiration time.
- The database connection URL (`DATABASE_URL`), which can support any database type compatible with SQLAlchemy.
- A function to create and configure an SQLModel database engine (`getEngine`).

Usage:
- Modify the `DATA_STORE` and `DOCUMENT_STORE` to use different backends as needed.
- Ensure the `JWT_SECRET_KEY` is securely managed.
- Adjust the `DATABASE_URL` for different database types or deployment environments.

Dependencies:
- `sqlmodel` for database interaction.
- `backends.filesystem` for file storage management.
"""

from sqlmodel import create_engine

from backends.filesystem.localfs import LocalFileSystem


# Storage backend settings

DATA_STORE = LocalFileSystem("./data")
"""
An instance of a file storage backend used as the primary data store for the application.
This can be configured to use any backend supported by `backends.filesystem`, such as LocalFileSystem, S3, or others.
In this case, it is set to use LocalFileSystem with the root directory "./data".
"""

DOCUMENT_STORE = LocalFileSystem("./data/documents")
"""
An instance of a file storage backend used specifically for document storage.
This can use any backend supported by `backends.filesystem`, such as LocalFileSystem, S3, or others.
Currently configured to use LocalFileSystem with the root directory "./data/documents".
"""

# JWT settings

JWT_SECRET_KEY = "your-secret-key"
"""
The secret key used for signing and verifying JSON Web Tokens (JWT).
Ensure this is kept secure and not exposed publicly.
"""

JWT_ALGORITHM = "HS256"
"""
The algorithm used for encoding and decoding JWTs. In this case, it uses the HS256 (HMAC with SHA-256) algorithm.
"""

JWT_EXPIRE_MINUTES = 30
"""
The expiration time (in minutes) for JWTs. Tokens will expire 30 minutes after being issued.
"""

# Database settings

DATABASE_URL = "sqlite:///" + (DATA_STORE.root / "db.sqlite").as_posix()
"""
The connection URL for the database used by the application.
This can be any database URL supported by SQLAlchemy, such as SQLite, PostgreSQL, MySQL, etc.
Currently configured to use SQLite with the database file stored in the root of the data store as "db.sqlite".
"""

def getEngine():
    """
    Creates and returns an SQLModel database engine for interacting with the database.
    
    The engine is configured to:
    - Use the connection URL defined in `DATABASE_URL`.
    - Disable query echoing (for cleaner logs).
    - Include `check_same_thread=False` to ensure compatibility in a multi-threaded environment when using SQLite.
    
    Returns:
        Engine: The SQLModel database engine.
    """
    return create_engine(
        DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
    )
