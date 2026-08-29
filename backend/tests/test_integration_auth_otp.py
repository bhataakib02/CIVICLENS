"""Integration tests for phone-based OTP authentication flow."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_otp_request_and_verify_flow(client):
    phone = "+919876543210"

    # 1. Request OTP
    resp = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
    assert resp.status_code == 202

    # 2. Verify OTP (TestOTPProvider uses fixed code '000000' in test env)
    resp = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "000000"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_otp_verify_invalid_code(client):
    phone = "+919876543211"
    client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

    resp = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "999999"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "OTP_INVALID"


def test_otp_verify_without_request(client):
    resp = client.post("/api/v1/auth/otp/verify", json={"phone_number": "+919999999999", "code": "000000"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "OTP_EXPIRED"
