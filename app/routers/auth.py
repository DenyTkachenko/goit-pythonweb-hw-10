from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..security import create_access_token, create_verify_token, verify_password, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")
    user = crud.create_user(db, payload)
    # генерує email-верифікаційний токен і "надіслати" лінк (для навчання — просто в консоль)
    token = create_verify_token(user.id)
    link = f"http://127.0.0.1:8000/auth/verify?token={token}"
    print(f"[DEV] Verify link for {user.email}: {link}")
    return user

@router.get("/verify", response_model=schemas.UserOut)
def verify_email(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "verify":
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.get(crud.models.User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if not user.is_verified:
        user.is_verified = True
        db.commit()
        db.refresh(user)
    return user

@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email is not verified")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
