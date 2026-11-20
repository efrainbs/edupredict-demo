from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut
from app.security import create_access_token, verify_password

router = APIRouter(tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        role=user.role,
        tutor_id=user.tutor_id,
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_session)],
) -> LoginResponse:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginResponse(
        access_token=create_access_token(user.id, user.role, user.tutor_id),
        user=_user_out(user),
    )


@router.get("/auth/me", response_model=UserOut)
def read_me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return _user_out(user)
