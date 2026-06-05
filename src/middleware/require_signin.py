from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from src.lib.auth import decode_token

bearer = HTTPBearer()


def require_signin(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    try:
        return decode_token(credentials.credentials)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
