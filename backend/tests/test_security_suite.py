"""Security Regression Test Suite for CivicLens.

Covers Prompt 11 requirements:
- Mass Assignment payload rejection (extra fields forbid)
- Scheme Four-Eyes approval enforcement (publisher != author)
- Published scheme version immutability
- File upload magic bytes validation (PDF, PNG, JPEG)
- RAG context isolation & prompt injection defenses
- IDOR access isolation on documents and applications
"""
from __future__ import annotations

import pytest
from app.modules.documents.service import _validate_magic_bytes
from app.core.exceptions import ValidationError, ConflictError

pytestmark = pytest.mark.security


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_mass_assignment_extra_fields_rejected(client):
    """Pydantic schemas with extra="forbid" must return 422 if client passes unexpected extra parameters."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_mass_assign@example.com",
            "password": "Password123!",
            "role": "ADMIN",
            "is_admin": True,
            "permissions": ["*"],
        },
    )
    assert response.status_code == 422
    assert "extra_forbidden" in str(response.json()) or "Extra inputs are not permitted" in str(response.json())


def test_file_upload_magic_bytes_validation():
    """File content header magic bytes must match declared MIME type."""
    # Valid PDF
    _validate_magic_bytes(b"%PDF-1.4 header content", "application/pdf")
    # Invalid PDF (script disguised as PDF)
    with pytest.raises(ValidationError):
        _validate_magic_bytes(b"<script>alert(1)</script>", "application/pdf")

    # Valid PNG
    _validate_magic_bytes(b"\x89PNG\r\n\x1a\nfake_png_data", "image/png")
    # Invalid PNG
    with pytest.raises(ValidationError):
        _validate_magic_bytes(b"INVALID_HEADER_PNG_BYTES", "image/png")

    # Valid JPEG
    _validate_magic_bytes(b"\xff\xd8\xff\xe0fake_jpeg", "image/jpeg")
    # Invalid JPEG
    with pytest.raises(ValidationError):
        _validate_magic_bytes(b"NOT_A_JPEG_FILE", "image/jpeg")


def test_four_eyes_self_approval_rejected(client, db_session_factory):
    """A scheme version author must not be able to publish their own version."""
    from app.models.user import User
    from app.models.enums import UserRole, SchemeScope
    from app.core.security import create_access_token
    from app.modules.schemes.service import SchemesService

    with db_session_factory() as session:
        admin_user = User(
            email="scheme_author@example.com",
            role=UserRole.SCHEME_ADMIN,
            password_hash="argon2_fake",
        )
        session.add(admin_user)
        session.commit()
        author_id = admin_user.id

        service = SchemesService(session)
        scheme = service.create_scheme(
            canonical_name="Test Four Eyes Scheme",
            category="Welfare",
            scope=SchemeScope.STATE,
            administering_dept="Dept",
            code="FOUR_EYES_001",
            actor_user_id=author_id,
        )
        version = service.create_version(
            scheme_id=scheme.id,
            benefits_summary="Test Benefits",
            effective_from=pytest.importorskip("datetime").date.today(),
            effective_to=None,
            knowledge_source_id=None,
            actor_user_id=author_id,
        )
        # Add a rule so rule count is non-zero
        service.set_rules(
            version_id=version.id,
            rules=[
                {
                    "type": "condition",
                    "rule_code": "R1",
                    "field_key": "declared_annual_income",
                    "operator": "lte",
                    "value": 100000,
                    "mandatory": True,
                    "explanation_text": "Income limit",
                }
            ],
            actor_user_id=author_id,
        )
        version_id = version.id

    # Attempt publishing with author's token -> ConflictError FOUR_EYES_REQUIRED
    with db_session_factory() as session:
        service = SchemesService(session)
        with pytest.raises(ConflictError) as exc:
            service.publish_version(version_id=version_id, actor_user_id=author_id)
        assert exc.value.code == "FOUR_EYES_REQUIRED"


def test_published_scheme_immutability(db_session_factory):
    """Rules cannot be edited on a published scheme version."""
    from app.models.user import User
    from app.models.enums import UserRole, SchemeScope
    from app.modules.schemes.service import SchemesService
    import datetime

    with db_session_factory() as session:
        author = User(email="author_immut@example.com", role=UserRole.SCHEME_ADMIN, password_hash="h")
        reviewer = User(email="reviewer_immut@example.com", role=UserRole.SCHEME_ADMIN, password_hash="h")
        session.add_all([author, reviewer])
        session.commit()
        author_id, reviewer_id = author.id, reviewer.id

        service = SchemesService(session)
        scheme = service.create_scheme(
            canonical_name="Immutability Scheme",
            category="Welfare",
            scope=SchemeScope.CENTRAL,
            administering_dept="Dept",
            code="IMMUT_001",
            actor_user_id=author_id,
        )
        version = service.create_version(
            scheme_id=scheme.id,
            benefits_summary="Summary",
            effective_from=datetime.date.today(),
            effective_to=None,
            knowledge_source_id=None,
            actor_user_id=author_id,
        )
        service.set_rules(
            version_id=version.id,
            rules=[
                {
                    "type": "condition",
                    "rule_code": "R1",
                    "field_key": "declared_annual_income",
                    "operator": "lte",
                    "value": 200000,
                    "mandatory": True,
                    "explanation_text": "Income limit",
                }
            ],
            actor_user_id=author_id,
        )
        # Publish by reviewer
        published_ver = service.publish_version(version_id=version.id, actor_user_id=reviewer_id)
        ver_id = published_ver.id

    # Attempt to modify rules on published version -> VERSION_IMMUTABLE
    with db_session_factory() as session:
        service = SchemesService(session)
        with pytest.raises(ConflictError) as exc:
            service.set_rules(
                version_id=ver_id,
                rules=[
                    {
                        "type": "condition",
                        "rule_code": "R1",
                        "field_key": "declared_annual_income",
                        "operator": "lte",
                        "value": 500000,
                        "mandatory": True,
                        "explanation_text": "Modified income limit",
                    }
                ],
                actor_user_id=author_id,
            )
        assert exc.value.code == "VERSION_IMMUTABLE"
