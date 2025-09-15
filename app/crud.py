from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from . import models, schemas
from .security import hash_password

# ===== Users =====
def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()

def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    user = models.User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ===== Contacts (scoped by owner_id) =====
def create_contact(db: Session, owner_id: int, data: schemas.ContactCreate) -> models.Contact:
    c = models.Contact(owner_id=owner_id, **data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def get_contact(db: Session, owner_id: int, contact_id: int) -> models.Contact | None:
    stmt = select(models.Contact).where(models.Contact.id == contact_id, models.Contact.owner_id == owner_id)
    return db.execute(stmt).scalar_one_or_none()

def get_contacts(db: Session, owner_id: int, *, q: str | None = None, first_name: str | None = None,
                 last_name: str | None = None, email: str | None = None, limit: int = 50, offset: int = 0
) -> Sequence[models.Contact]:
    stmt = select(models.Contact).where(models.Contact.owner_id == owner_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(models.Contact.first_name.ilike(like),
                              models.Contact.last_name.ilike(like),
                              models.Contact.email.ilike(like)))
    else:
        if first_name: stmt = stmt.where(models.Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:  stmt = stmt.where(models.Contact.last_name.ilike(f"%{last_name}%"))
        if email:      stmt = stmt.where(models.Contact.email.ilike(f"%{email}%"))
    stmt = stmt.order_by(models.Contact.id).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()

def update_contact_put(db: Session, contact: models.Contact, data: schemas.ContactUpdatePut) -> models.Contact:
    for k, v in data.model_dump().items(): setattr(contact, k, v)
    db.commit(); db.refresh(contact); return contact

def update_contact_patch(db: Session, contact: models.Contact, data: schemas.ContactUpdatePatch) -> models.Contact:
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(contact, k, v)
    db.commit(); db.refresh(contact); return contact

def delete_contact(db: Session, contact: models.Contact) -> None:
    db.delete(contact); db.commit()
