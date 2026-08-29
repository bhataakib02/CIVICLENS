"""Unit tests: password hashing, JWT, email normalization, password policy.

Pure-function tests — no database required.
"""
from __future__ import annotations

import time
from datetime import timedelta

import pytest

from app.core.exceptions import InvalidTokenError, ValidationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_password_policy,
    verify_password,
)
from app.modules.auth.service import normalize_email

pytestmark = pytest.mark.unit


def test_password_hash_is_argon2id_and_not_plaintext():
    pw = "CorrectHorseBattery9!"
    h = hash_password(pw)
    assert h.startswith("$argon2id$")
    assert pw not in h


def test_password_verify_roundtrip():
    pw = "CorrectHorseBattery9!"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("wrong-password-1234", h) is False


def test_password_hashes_are_salted_unique():
    pw = "CorrectHorseBattery9!"
    assert hash_password(pw) != hash_password(pw)


def test_verify_rejects_garbage_hash_without_raising():
    assert verify_password("anything", "not-a-valid-hash") is False


def test_jwt_create_and_decode_claims():
    token, expires_in = create_access_token(subject="user-123", role="citizen")
    assert expires_in == 15 * 60
    claims = decode_access_token(token)
    assert claims["sub"] == "user-123"
    assert claims["role"] == "citizen"
    assert claims["type"] == "access"
    assert claims["iss"] == "civiclens"
    assert "jti" in claims and "iat" in claims and "exp" in claims


def test_jwt_expired_token_rejected():
    token, _ = create_access_token(
        subject="u", role="citizen", expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_jwt_tampered_token_rejected():
    token, _ = create_access_token(subject="u", role="citizen")
    tampered = token[:-3] + ("aaa" if token[-3:] != "aaa" else "bbb")
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_jwt_wrong_secret_rejected():
    from app.core.config import Settings

    other = Settings(jwt_secret_key="a-different-secret-entirely-999999999999")
    token, _ = create_access_token(subject="u", role="citizen")  # signed with default test secret
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, settings=other)


def test_refresh_token_opaque_and_hash_deterministic():
    raw = generate_refresh_token()
    assert len(raw) >= 40
    assert not raw.startswith("ey")  # not a JWT
    assert hash_refresh_token(raw) == hash_refresh_token(raw)
    assert hash_refresh_token(raw) != raw


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Citizen@Example.com", "citizen@example.com"),
        ("  USER@Domain.COM  ", "user@domain.com"),
        ("already@lower.com", "already@lower.com"),
    ],
)
def test_email_normalization(raw, expected):
    assert normalize_email(raw) == expected


def test_password_policy_min_length():
    with pytest.raises(ValidationError):
        validate_password_policy("Short1!")  # < 12 chars


def test_password_policy_requires_complexity():
    with pytest.raises(ValidationError):
        validate_password_policy("aaaaaaaaaaaaaaaa")  # only one class


def test_password_policy_accepts_strong_password():
    validate_password_policy("CorrectHorse9Battery!")  # no raise


def test_production_config_validation_otp_provider():
    from app.core.config import Settings

    s = Settings(
        environment="production",
        jwt_secret_key="a-very-long-production-jwt-secret-key-32chars",
        cors_origins_raw="https://app.civiclens.gov.in",
        storage_provider="s3",
        ocr_provider="aws_textract",
        submission_provider="state_api",
        otp_provider="test",
    )
    with pytest.raises(ValueError, match="OTP_PROVIDER"):
        s.validate_production_config()

