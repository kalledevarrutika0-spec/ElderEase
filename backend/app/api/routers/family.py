from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_supabase_user_id
from app.database import get_db
from app.schemas.family import (
    FamilyMemberLink,
    FamilyProfileCreate,
    FamilyProfileRead,
    FamilyProfileUpdate,
)
from app.services.family_service import (
    create_family_profile,
    get_family_profile,
    link_family_member,
    update_family_profile,
)

router = APIRouter(prefix="/family", tags=["family"])


@router.get("/profile", response_model=FamilyProfileRead)
def read_profile(
    user_id: str = Depends(get_supabase_user_id),
    session: Session = Depends(get_db),
) -> FamilyProfileRead:
    return get_family_profile(session, user_id)


@router.post("/profile", response_model=FamilyProfileRead)
def create_profile(
    data: FamilyProfileCreate,
    user_id: str = Depends(get_supabase_user_id),
    session: Session = Depends(get_db),
) -> FamilyProfileRead:
    return create_family_profile(session, user_id, data)


@router.put("/profile", response_model=FamilyProfileRead)
def edit_profile(
    data: FamilyProfileUpdate,
    user_id: str = Depends(get_supabase_user_id),
    session: Session = Depends(get_db),
) -> FamilyProfileRead:
    return update_family_profile(session, user_id, data)


@router.post("/members/link", response_model=FamilyProfileRead)
def link_member(
    data: FamilyMemberLink,
    user_id: str = Depends(get_supabase_user_id),
    session: Session = Depends(get_db),
) -> FamilyProfileRead:
    return link_family_member(session, user_id, data)
