import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SenderProfile
from app.schemas import SenderProfileCreate, SenderProfileOut, SenderProfileUpdate

logger = logging.getLogger("paperless-letter-generator.senders")
router = APIRouter(prefix="/api/sender-profiles", tags=["sender-profiles"])


@router.get("", response_model=list[SenderProfileOut])
def list_senders(db: Session = Depends(get_db)):
    return db.query(SenderProfile).order_by(SenderProfile.name).all()


@router.post("", response_model=SenderProfileOut, status_code=201)
def create_sender(body: SenderProfileCreate, db: Session = Depends(get_db)):
    if body.is_default:
        db.query(SenderProfile).update({"is_default": 0})
    profile = SenderProfile(
        name=body.name,
        street=body.street,
        zip_city=body.zip_city,
        country=body.country,
        email=body.email,
        phone=body.phone,
        is_default=1 if body.is_default else 0,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=SenderProfileOut)
def get_sender(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(SenderProfile).filter(SenderProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Sender profile not found")
    return profile


@router.put("/{profile_id}", response_model=SenderProfileOut)
def update_sender(profile_id: int, body: SenderProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(SenderProfile).filter(SenderProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Sender profile not found")
    if body.is_default is not None and body.is_default:
        db.query(SenderProfile).filter(SenderProfile.id != profile_id).update({"is_default": 0})
    update_data = body.model_dump(exclude_unset=True)
    if "is_default" in update_data:
        update_data["is_default"] = 1 if update_data["is_default"] else 0
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_sender(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(SenderProfile).filter(SenderProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Sender profile not found")
    db.delete(profile)
    db.commit()


@router.get("/default", response_model=SenderProfileOut)
def get_default_sender(db: Session = Depends(get_db)):
    profile = db.query(SenderProfile).filter(SenderProfile.is_default == 1).first()
    if not profile:
        raise HTTPException(404, "No default sender profile set")
    return profile
