from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ===== Users/Auth =====
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserOut(UserBase):
    id: int
    is_verified: bool
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ===== Contacts =====
class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str  = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=50)
    birthday: date
    extra: str | None = None

class ContactCreate(ContactBase): pass
class ContactUpdatePut(ContactBase): pass

class ContactUpdatePatch(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=3, max_length=50)
    birthday: date | None = None
    extra: str | None = None

class ContactOut(ContactBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)