from fastapi import status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from models.document import Document
from helpers.jwt_token import decode_access_token
from models.user import User, UserWithPrivateKey

API_TOKEN_ROUTE_NAME = "token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=API_TOKEN_ROUTE_NAME)


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Retrieves the current user from the token."""
    username, password = decode_access_token(token)
    user = User.get(username)
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    private_key = user.get_private_key(password)
    return UserWithPrivateKey(user=user, private_key=private_key)


def get_doc_and_user(
    doc_id: str, user_and_key: UserWithPrivateKey = Depends(get_current_user)
):
    doc = Document.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return doc, user_and_key


def get_doc_and_accessor(doc_and_user: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_user)):
    doc, user_and_key = doc_and_user
    if user_and_key.user.id not in doc.shared_with:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document",
        )
    return doc_and_user


def get_doc_and_owner(
    doc_and_user: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_user),
):
    doc, user_and_key = doc_and_user

    if user_and_key.user.id != doc.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this document",
        )
    return doc_and_user
