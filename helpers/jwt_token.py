from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from config import JWT_ALGORITHM, JWT_SECRET_KEY, JWT_EXPIRE_MINUTES


def create_access_token(
    data: dict, expires_delta: timedelta = timedelta(minutes=JWT_EXPIRE_MINUTES)
):
    """Generates a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _get_exception(detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def decode_access_token(token: str) -> tuple[str, str]:
    """Decodes and validates a JWT token. Returns the username and password."""
    try:
        payload: dict = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("username")
        password: str = payload.get("password")
        if username is None:
            raise _get_exception("Invalid token payload")
        return username, password
    except jwt.ExpiredSignatureError:
        raise _get_exception("Token has expired")
    except jwt.exceptions.PyJWTError:
        raise _get_exception("Invalid token")
