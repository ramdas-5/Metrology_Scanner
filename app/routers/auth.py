from fastapi import APIRouter, Depends, HTTPException, status

from app import crud, models, schemas
from app import auth as auth_utils

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _role_value(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate):
    if crud.get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    if payload.role not in [r.value for r in models.UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = crud.create_user(
        name=payload.name,
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
        role=payload.role,
    )
    crud.add_audit_log(user["id"], "USER_REGISTERED", f"Account created for {payload.email}")
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest):
    user = crud.get_user_by_email(payload.email)
    if not user or not auth_utils.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = auth_utils.create_access_token({"sub": user.id, "role": _role_value(user.role)})
    crud.add_audit_log(user.id, "USER_LOGIN", f"{user.email} signed in")
    return schemas.Token(access_token=token, user=user)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.Doc = Depends(auth_utils.get_current_user)):
    return current_user


@router.post("/refresh", response_model=schemas.Token)
def refresh(current_user: models.Doc = Depends(auth_utils.get_current_user)):
    """
    Hand back a fresh token for the caller. The frontend calls this once a day
    while the app is open, so an active session never expires mid-work (and a
    short backend restart does not log anyone out).
    """
    token = auth_utils.create_access_token(
        {"sub": current_user.id, "role": _role_value(current_user.role)}
    )
    return schemas.Token(access_token=token, user=current_user)


@router.post("/logout")
def logout(current_user: models.Doc = Depends(auth_utils.get_current_user)):
    """JWTs are stateless; the client clears its stored token. Logged for audit."""
    crud.add_audit_log(current_user.id, "USER_LOGOUT", f"{current_user.email} signed out")
    return {"detail": "Logged out"}
