import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Caregiver, FamilyMember, FamilyProfile
from app.schemas.family import (
    FamilyMemberLink,
    FamilyProfileCreate,
    FamilyProfileUpdate,
)
from app.services.errors import ConflictError, NotFoundError


def _invite_code() -> str:
    return secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:12].upper()


def get_family_profile(session: Session, user_id: str) -> FamilyProfile:
    member = session.scalar(
        select(FamilyMember).where(FamilyMember.auth_user_id == user_id)
    )
    if member is None:
        raise NotFoundError("Family profile has not been created.")
    profile = session.get(FamilyProfile, member.family_id)
    if profile is None:
        raise NotFoundError("Family profile was not found.")
    return profile


def create_family_profile(
    session: Session,
    user_id: str,
    data: FamilyProfileCreate,
) -> FamilyProfile:
    existing = session.scalar(
        select(FamilyMember).where(FamilyMember.auth_user_id == user_id)
    )
    if existing is not None:
        raise ConflictError("This account already belongs to a family care profile.")

    try:
        with session.begin():
            caregiver = Caregiver(
                name=data.caregiver_name.strip(),
                relationship=data.relationship.strip(),
                auth_user_id=user_id,
            )
            session.add(caregiver)
            session.flush()
            caregiver.family_id = profile.id

            profile = FamilyProfile(
                family_name=data.family_name.strip(),
                elder_name=data.elder_name.strip(),
                elder_age=data.elder_age,
                elder_care_notes=(
                    data.elder_care_notes.strip()
                    if data.elder_care_notes
                    else None
                ),
                invite_code=_invite_code(),
                primary_caregiver_id=caregiver.id,
            )
            session.add(profile)
            session.flush()
            caregiver.family_id = profile.id

            session.add(
                FamilyMember(
                    family_id=profile.id,
                    caregiver_id=caregiver.id,
                    auth_user_id=user_id,
                    role=data.role.strip(),
                    relationship=data.relationship.strip(),
                    is_primary=True,
                )
            )
    except IntegrityError as exc:
        raise ConflictError("The family profile could not be created.") from exc
    return profile


def update_family_profile(
    session: Session,
    user_id: str,
    data: FamilyProfileUpdate,
) -> FamilyProfile:
    profile = get_family_profile(session, user_id)
    member = session.scalar(
        select(FamilyMember).where(FamilyMember.auth_user_id == user_id)
    )
    if member is None or not member.is_primary:
        raise ConflictError("Only the primary caregiver can edit the family profile.")

    profile.family_name = data.family_name.strip()
    profile.elder_name = data.elder_name.strip()
    profile.elder_age = data.elder_age
    profile.elder_care_notes = (
        data.elder_care_notes.strip() if data.elder_care_notes else None
    )
    session.commit()
    session.refresh(profile)
    return profile


def link_family_member(
    session: Session,
    user_id: str,
    data: FamilyMemberLink,
) -> FamilyProfile:
    existing = session.scalar(
        select(FamilyMember).where(FamilyMember.auth_user_id == user_id)
    )
    if existing is not None:
        raise ConflictError("This account already belongs to a family care profile.")

    profile = session.scalar(
        select(FamilyProfile).where(
            FamilyProfile.invite_code == data.invite_code.strip().upper()
        )
    )
    if profile is None:
        raise NotFoundError("The family invite code was not found.")

    try:
        with session.begin():
            caregiver = Caregiver(
                name=data.caregiver_name.strip(),
                relationship=data.relationship.strip(),
                auth_user_id=user_id,
            )
            session.add(caregiver)
            session.flush()
            session.add(
                FamilyMember(
                    family_id=profile.id,
                    caregiver_id=caregiver.id,
                    auth_user_id=user_id,
                    role=data.role.strip(),
                    relationship=data.relationship.strip(),
                    is_primary=False,
                )
            )
    except IntegrityError as exc:
        raise ConflictError("The caregiver could not join this family.") from exc
    return profile
