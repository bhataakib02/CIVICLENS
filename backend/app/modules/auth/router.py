"""Auth + current-user HTTP routes.

Endpoints (email/password auth is a documented contract extension — see
openapi.yaml and the implementation report):
    POST   /auth/register
    POST   /auth/login
    POST   /auth/refresh
    POST   /auth/logout
    GET    /me           (account identity view)

Routers translate HTTP <-> application commands only; business rules live in
AuthService (docs/backend/service-layer.md).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.schemas.auth import (
    LoginInput,
    MeResponse,
    RefreshInput,
    RegisterInput,
    TokenPair,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["profile"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


@auth_router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterInput,
    request: Request,
    session: Session = Depends(db_session),
) -> TokenPair:
    return AuthService(session).register(body.email, body.password, ip=_client_ip(request))


@auth_router.post("/login", response_model=TokenPair)
def login(
    body: LoginInput,
    request: Request,
    session: Session = Depends(db_session),
) -> TokenPair:
    return AuthService(session).login(body.email, body.password, ip=_client_ip(request))


@auth_router.post("/refresh", response_model=TokenPair)
def refresh(
    body: RefreshInput,
    request: Request,
    session: Session = Depends(db_session),
) -> TokenPair:
    return AuthService(session).refresh(body.refresh_token, ip=_client_ip(request))


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    body: RefreshInput | None = None,
    all: bool = False,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> Response:
    raw = body.refresh_token if body else None
    AuthService(session).logout(
        raw, current.id, all_sessions=all, ip=_client_ip(request)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@me_router.get("/me/account", response_model=MeResponse)
def get_me_account(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> MeResponse:
    """Account-level identity view (documented extension).

    The contract's GET /me returns the CitizenProfile (served by the citizens
    router); this exposes the account identity (email/role/status) which the
    email/password extension needs. Contains no secrets."""
    user = AuthRepository(session).get_user_by_id(current.id)
    # current is derived from a validated token; user is guaranteed present.
    assert user is not None
    return MeResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        role=user.role.value,
        status=user.status.value,
    )
