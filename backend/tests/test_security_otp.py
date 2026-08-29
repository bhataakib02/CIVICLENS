"""Security tests for phone-based OTP authentication."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.security


def test_otp_single_use_replay_prevention(client):
    phone = "+919876543222"
    client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

    # First verify: success
    resp1 = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "000000"})
    assert resp1.status_code == 200

    # Second verify with same OTP: fails (single-use enforcement)
    resp2 = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "000000"})
    assert resp2.status_code == 401
    assert resp2.json()["error"]["code"] == "OTP_EXPIRED"


def test_otp_attempt_limits(client):
    phone = "+919876543333"
    client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

    # Submit wrong code 5 times
    for _ in range(5):
        resp = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "111111"})
        assert resp.status_code == 401

    # 6th attempt even with correct code must be rejected (max attempts reached)
    resp = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "000000"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] in ("OTP_MAX_ATTEMPTS", "OTP_EXPIRED")
