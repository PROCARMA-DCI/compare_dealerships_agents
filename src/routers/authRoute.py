from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from src.lib.auth import create_token, hash_password, verify_password
from src.lib.auth_db import get_auth_session
from src.middleware.require_signin import require_signin
from src.models.user import User
from src.schemas.auth_schema import (
    RegisterRequest,
    SignInRequest,
    SignInResponse,
    UpdatePasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

DEFAULT_PASSWORD = "12345"


@router.post("/init", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_auth_session)):
    user_count = session.exec(select(func.count()).select_from(User)).one()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is closed. Only one account is allowed.",
        )
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password or DEFAULT_PASSWORD),
    )
    session.add(user)
    session.commit()
    return {
        "success": True,
        "message": f"Account created.",
    }


@router.post("/signin", response_model=SignInResponse)
def signin(payload: SignInRequest, session: Session = Depends(get_auth_session)):
    user = session.exec(select(User).where(User.username == payload.username)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return SignInResponse(token=create_token(user.username), username=user.username)


@router.put("/update-password")
def update_password(
    payload: UpdatePasswordRequest,
    username: str = Depends(require_signin),
    session: Session = Depends(get_auth_session),
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.hashed_password = hash_password(payload.new_password)
    session.add(user)
    session.commit()
    return {"success": True, "message": "Password updated"}
