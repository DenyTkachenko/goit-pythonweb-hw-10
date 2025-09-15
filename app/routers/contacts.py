from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..models import User
from .users import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = crud.get_contacts(db, current_user.id, email=payload.email, limit=1)
    if items:
        raise HTTPException(status_code=409, detail="Contact email already exists")
    return crud.create_contact(db, current_user.id, payload)

@router.get("", response_model=list[schemas.ContactOut])
def list_contacts(
    q: str | None = Query(None),
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_contacts(db, current_user.id, q=q, first_name=first_name, last_name=last_name, email=email, limit=limit, offset=offset)

@router.get("/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = crud.get_contact(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=schemas.ContactOut)
def update_contact_put(contact_id: int, payload: schemas.ContactUpdatePut, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = crud.get_contact(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if payload.email != contact.email:
        items = crud.get_contacts(db, current_user.id, email=payload.email, limit=1)
        if items:
            raise HTTPException(status_code=409, detail="Contact email already exists")
    return crud.update_contact_put(db, contact, payload)

@router.patch("/{contact_id}", response_model=schemas.ContactOut)
def update_contact_patch(contact_id: int, payload: schemas.ContactUpdatePatch, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = crud.get_contact(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if payload.email and payload.email != contact.email:
        items = crud.get_contacts(db, current_user.id, email=payload.email, limit=1)
        if items:
            raise HTTPException(status_code=409, detail="Contact email already exists")
    return crud.update_contact_patch(db, contact, payload)

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = crud.get_contact(db, current_user.id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    crud.delete_contact(db, contact)
    return None

@router.get("/upcoming-birthdays", response_model=list[schemas.ContactOut])
def upcoming_birthdays(days: int = Query(7, ge=1, le=366), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import extract, or_, func, select
    from ..models import Contact

    today_md = func.extract("month", func.current_date()) * 100 + func.extract("day", func.current_date())
    end_date = func.current_date() + func.make_interval(days=days)
    end_md = func.extract("month", end_date) * 100 + func.extract("day", end_date)
    birthday_md = extract("month", Contact.birthday) * 100 + extract("day", Contact.birthday)
    same_year_span = today_md <= end_md

    stmt_same = select(Contact).where(Contact.owner_id == current_user.id, birthday_md.between(today_md, end_md))
    stmt_wrap = select(Contact).where(Contact.owner_id == current_user.id).where(or_(birthday_md >= today_md, birthday_md <= end_md))
    stmt = stmt_same if same_year_span else stmt_wrap
    stmt = stmt.order_by(birthday_md, Contact.last_name, Contact.first_name)

    return list(db.execute(stmt).scalars().all())
