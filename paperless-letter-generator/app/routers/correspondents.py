import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CorrespondentProfile
from app.schemas import (
    CorrespondentProfileCreate,
    CorrespondentProfileOut,
    CorrespondentProfileUpdate,
)

logger = logging.getLogger("paperless-letter-generator.correspondents")
router = APIRouter(prefix="/api/correspondent-profiles", tags=["correspondent-profiles"])


@router.get("", response_model=list[CorrespondentProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(CorrespondentProfile).order_by(CorrespondentProfile.name).all()


@router.post("", response_model=CorrespondentProfileOut, status_code=201)
def create_profile(body: CorrespondentProfileCreate, db: Session = Depends(get_db)):
    if body.paperless_id is not None:
        existing = db.query(CorrespondentProfile).filter(
            CorrespondentProfile.paperless_id == body.paperless_id
        ).first()
        if existing:
            raise HTTPException(409, "Profile already exists for this correspondent")
    profile = CorrespondentProfile(**body.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=CorrespondentProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(CorrespondentProfile).filter(CorrespondentProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


@router.put("/{profile_id}", response_model=CorrespondentProfileOut)
def update_profile(profile_id: int, body: CorrespondentProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(CorrespondentProfile).filter(CorrespondentProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(CorrespondentProfile).filter(CorrespondentProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    db.delete(profile)
    db.commit()


@router.get("/by-paperless/{paperless_id}", response_model=CorrespondentProfileOut)
def get_profile_by_paperless(paperless_id: int, db: Session = Depends(get_db)):
    profile = db.query(CorrespondentProfile).filter(
        CorrespondentProfile.paperless_id == paperless_id
    ).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile
