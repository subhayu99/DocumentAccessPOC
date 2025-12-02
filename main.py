from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import FastAPI, Depends, HTTPException, Query, status, UploadFile

from config import JWT_EXPIRE_MINUTES
from helpers.jwt_token import create_access_token
from models.document import Document, DocumentBase, DocumentShareResponse
from models.user import User, UserBase, UserCreateResponse, UserWithPrivateKey
from logic.deps import get_current_user, get_doc_and_owner, get_doc_and_accessor, API_TOKEN_ROUTE_NAME

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # Adjust to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(f"/{API_TOKEN_ROUTE_NAME}")
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


@app.post("/users", response_model=UserCreateResponse)
def create_user(user: UserBase):
    user = User.from_base(user)
    return user


@app.get("/users/me", response_model=User)
def get_my_profile(user_and_key: UserWithPrivateKey = Depends(get_current_user)):
    return user_and_key.user


@app.get("/users", response_model=list[UserBase])
def get_user_profiles(user_ids: list[str] = Query(default_factory=list)):
    users = User().get_by_ids(user_ids)
    return [UserBase.model_validate(x) for x in users]


@app.post("/documents", response_model=DocumentShareResponse)
def upload_document(
    file: UploadFile,
    share_with: list[str] = Query(default_factory=list, description="User IDs to share with"),
    user_and_key: UserWithPrivateKey = Depends(get_current_user),
):
    doc = DocumentBase(
        filepath=file.filename,
        content=file.file.read(),
        owner_id=user_and_key.user.id,
        share_with=share_with,
    )
    uploaded_doc = Document.upload(doc)
    return uploaded_doc


@app.get("/documents/{doc_id}")
async def download_document(
    doc_and_accessor: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_accessor),
):
    doc, user_and_key = doc_and_accessor
    downloaded_doc = doc.download(
        user_and_key.user.id, user_and_key.private_key.encode()
    )
    filename = downloaded_doc.filepath.split("/")[-1]
    return StreamingResponse(
        iter([downloaded_doc.content]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Filename": filename,
            "Access-Control-Expose-Headers": "Content-Disposition, filename",
        },
    )


@app.put("/documents/{doc_id}/share", response_model=DocumentShareResponse)
def share_document(
    share_with: list[str] = Query(default_factory=list, description="User IDs to share with"),
    doc_and_owner: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_owner),
):
    doc, user_and_key = doc_and_owner
    response = doc.share(share_with, user_and_key.private_key)
    return response


@app.put("/documents/{doc_id}/revoke", response_model=DocumentShareResponse)
def revoke_document(
    revoke: list[str] = Query(default_factory=list, description="User IDs to revoke access from"),
    doc_and_owner: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_owner),
):
    doc, owner = doc_and_owner
    response = doc.revoke_access(revoke, owner.private_key)
    return response


@app.delete("/documents/{doc_id}")
def delete_document(doc_and_owner: tuple[Document, UserWithPrivateKey] = Depends(get_doc_and_owner)):
    doc, _ = doc_and_owner
    doc.delete()
    return JSONResponse(
        content={"message": "Document deleted"}, status_code=status.HTTP_204_NO_CONTENT
    )


@app.get("/documents", response_model=list[Document])
def list_documents(user_and_key: UserWithPrivateKey = Depends(get_current_user)):
    documents = Document.get_shared_documents(user_and_key.user.id)
    return documents


# Start the FastAPI server by running:
# uvicorn main:app --reload
