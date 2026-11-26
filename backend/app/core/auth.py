from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import jwt
from jwt import PyJWKClient

from app.core.config import settings
from app.database import get_db
from app.models import FamilyMember


def _unauthorized(detail: str = "Authentication required.") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def get_supabase_user_id(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise _unauthorized()

    try:
        if settings.supabase_jwt_secret:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                audience="authenticated",
            )
        elif settings.supabase_url:
            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
            )
        else:
            raise HTTPException(
                status_code=503,
                detail="Supabase authentication is not configured.",
            )
    except jwt.PyJWTError as exc:
        raise _unauthorized("The Supabase session is invalid or expired.") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("The Supabase session has no user identity.")
    return str(user_id)


def get_family_member(
    user_id: str = Depends(get_supabase_user_id),
    session: Session = Depends(get_db),
) -> FamilyMember:
    member = session.scalar(
        select(FamilyMember).where(FamilyMember.auth_user_id == user_id)
    )
    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Complete your family profile before continuing.",
        )
    return member


