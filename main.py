from datetime import timedelta
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, Form, HTTPException, status, UploadFile

from config import JWT_EXPIRE_MINUTES
from logic.login import create_access_token, decode_access_token
from models.document import Document, DocumentBase
from models.user import User, UserBase, UserCreateResponse, UserWithPrivateKey

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency to get the current user
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


# Route for OAuth2 login
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = User.get(form_data.username)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": form_data.username, "password": form_data.password}, 
        expires_delta=access_token_expires, 
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Simulate the user creation route (this will be handled separately in the provided user creation logic)
@app.post("/users/", response_model=UserCreateResponse)
def create_user(user: UserBase):
    user = User.from_base(user)
    return user


@app.get("/users", response_model=User)
def get_my_profile(user_and_key: UserWithPrivateKey = Depends(get_current_user)):
    return user_and_key.user.model_dump()


# Route to upload a document
@app.post("/documents", response_model=Document)
def upload_document(
    file: UploadFile,
    share_with: list[str] = Form(default_factory=list),
    user_and_key: UserWithPrivateKey = Depends(get_current_user),
):
    doc = DocumentBase(
        filepath=file.filename,
        content=file.file.read(),
        owner_id=user_and_key.user.id,
        give_access_to=share_with,
    )
    uploaded_doc = Document.upload(doc)
    return uploaded_doc


# Route to download a document
@app.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: str, user_and_key: UserWithPrivateKey = Depends(get_current_user)
):
    doc = Document.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    # Check if the user has access to the document
    if user_and_key.user.id not in doc.users_with_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document",
        )
    downloaded_doc = doc.download(
        user_and_key.user.id, user_and_key.private_key.encode()
    )
    return StreamingResponse(
        iter([downloaded_doc.content]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={downloaded_doc.filepath.split('/')[-1]}"},
    )


# Route to share a document with other users
@app.post("/documents/{doc_id}/share")
def share_document(
    doc_id: str,
    user_ids: list[str] = Form(default_factory=list),
    user_and_key: UserWithPrivateKey = Depends(get_current_user),
):
    doc = Document.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    # Check if the user is the owner of the document
    if user_and_key.user.id != doc.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this document",
        )
    doc.share(user_ids, user_and_key.private_key)
    return {
        "message": "Document shared successfully",
        "users_with_access": doc.users_with_access,
    }


# Route to list documents that a user has access to
@app.get("/documents/", response_model=list[Document])
def list_document_ids(user_and_key: UserWithPrivateKey = Depends(get_current_user)):
    documents_ids = Document.get_shared_documents(user_and_key.user.id)
    return documents_ids


# Start the FastAPI server by running:
# uvicorn main:app --reload
