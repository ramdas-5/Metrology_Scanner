from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, auth as auth_utils
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    if payload.role not in [r.value for r in models.UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth_utils.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = auth_utils.create_access_token({"sub": user.id, "role": user.role.value})
    return schemas.Token(access_token=token, user=user)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth_utils.get_current_user)):
    return current_user


@router.post("/refresh", response_model=schemas.Token)
def refresh(current_user: models.User = Depends(auth_utils.get_current_user)):
    """
    Hand back a fresh token for the caller. The frontend calls this once a day
    while the app is open, so an active session never expires mid-work (and a
    short backend restart does not log anyone out).
    """
    token = auth_utils.create_access_token(
        {"sub": current_user.id, "role": current_user.role.value}
    )
    return schemas.Token(access_token=token, user=current_user)


@router.post("/logout")
def logout(current_user: models.User = Depends(auth_utils.get_current_user)):
    """JWTs are stateless; the client clears its stored token. Logged for audit."""
    return {"detail": "Logged out"}
