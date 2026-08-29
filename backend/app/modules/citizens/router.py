"""Citizen profile + address HTTP routes.

Contract endpoints:
    GET   /me               -> CitizenProfile
    PATCH /me               -> update profile (progressive profiling)
    GET   /me/addresses     -> list
    POST  /me/addresses     -> create

Documented contract extensions (see openapi.yaml + report):
    PUT    /me/profile              (alias of PATCH /me — prompt requested PUT)
    PATCH  /me/profile
    GET    /me/profile
    PUT    /me/addresses/{id}       (update)
    DELETE /me/addresses/{id}       (delete)

Ownership is enforced in CitizensService from the authenticated principal.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.citizens.service import CitizensService
from app.schemas.citizen import (
    Address,
    AddressInput,
    AddressUpdate,
    CitizenProfile,
    CitizenProfileUpdate,
)

router = APIRouter(tags=["profile"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# --------------------------------- Profile ---------------------------------- #
@router.get("/me", response_model=CitizenProfile)
@router.get("/me/profile", response_model=CitizenProfile)
def get_profile(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> CitizenProfile:
    return CitizensService(session).get_profile(current.id)


@router.patch("/me", response_model=CitizenProfile)
@router.patch("/me/profile", response_model=CitizenProfile)
@router.put("/me/profile", response_model=CitizenProfile)
def update_profile(
    body: CitizenProfileUpdate,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> CitizenProfile:
    return CitizensService(session).update_profile(current.id, body, ip=_client_ip(request))


# --------------------------------- Addresses -------------------------------- #
@router.get("/me/addresses", response_model=list[Address])
def list_addresses(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> list[Address]:
    return CitizensService(session).list_addresses(current.id)


@router.post("/me/addresses", response_model=Address, status_code=status.HTTP_201_CREATED)
def create_address(
    body: AddressInput,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> Address:
    return CitizensService(session).create_address(current.id, body, ip=_client_ip(request))


@router.put("/me/addresses/{address_id}", response_model=Address)
def update_address(
    address_id: uuid.UUID,
    body: AddressUpdate,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> Address:
    return CitizensService(session).update_address(
        current.id, address_id, body, ip=_client_ip(request)
    )


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_address(
    address_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
):
    CitizensService(session).delete_address(current.id, address_id, ip=_client_ip(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
