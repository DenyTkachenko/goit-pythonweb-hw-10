import time
from collections import deque
from threading import RLock
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
import cloudinary, cloudinary.uploader

from ..database import get_db
from ..config import settings
from ..schemas import UserOut
from ..models import User
from ..security import decode_token

router = APIRouter(prefix="/users", tags=["users"])

# ---- auth dependency ----
def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email is not verified")
    return user

# ---- very simple in-memory rate limiter (per-process) ----
_REQS: dict[int, deque[float]] = {}
_LOCK = RLock()
LIMIT = 5   # times
WINDOW = 60 # seconds

def rate_limit(current_user: User = Depends(get_current_user)):
    now = time.time()
    with _LOCK:
        dq = _REQS.setdefault(current_user.id, deque())
        while dq and now - dq[0] > WINDOW:
            dq.popleft()
        if len(dq) >= LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        dq.append(now)

@router.get("/me", response_model=UserOut, dependencies=[Depends(rate_limit)])
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/avatar", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Cloudinary config
    if settings.CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
    else:
        if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
            raise HTTPException(status_code=500, detail="Cloudinary is not configured")
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    result = cloudinary.uploader.upload(
        file.file,
        folder="contacts_api/avatars",
        public_id=f"user_{current_user.id}",
        overwrite=True,
        resource_type="image",
    )
    current_user.avatar_url = result.get("secure_url")
    current_user.avatar_public_id = result.get("public_id")
    db.commit()
    db.refresh(current_user)
    return current_user
