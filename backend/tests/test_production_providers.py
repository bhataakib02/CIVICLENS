"""Unit & Mock Integration tests for production providers.

Tests OTP, Notification, Government API, LLM, and OCR production provider implementations
and ensures production configuration boundaries are strictly enforced.
"""
import pytest

from app.core.config import Settings
from app.models.enums import NotificationChannel
from app.modules.auth.otp_provider import (
    AWSSNSOTPProvider,
    Fast2SMSOTPProvider,
    OTPDeliveryError,
    ProductionSMSOTPProvider,
    TwilioOTPProvider,
    get_otp_provider,
)
from app.modules.notifications.providers import (
    AWSSESEmailProvider,
    AWSSNSNotificationProvider,
    ProviderUnavailableError,
    SendGridEmailProvider,
    SMTPEmailProvider,
    TwilioSMSNotificationProvider,
    get_provider,
)
from app.modules.notifications.providers.base import OutboundMessage
from app.modules.applications.submission import (
    DigiLockerSubmissionProvider,
    StatePortalApiSubmissionProvider,
    SubmissionProviderUnavailableError,
    get_submission_provider,
)
from app.modules.knowledge.llm.provider import (
    AnthropicLLMProvider,
    AWSBedrockLLMProvider,
    LLMError,
    OllamaLLMProvider,
    OpenAILLMProvider,
    get_llm_provider,
)
from app.modules.documents.processing.ocr import (
    AWSTextractOCRProvider,
    OCRUnavailableError,
    TesseractOCRProvider,
    get_ocr_provider,
)


def test_otp_provider_factory():
    s_sns = Settings(otp_provider="aws_sns", environment="test")
    p_sns = get_otp_provider(s_sns)
    assert isinstance(p_sns, AWSSNSOTPProvider)

    s_twilio = Settings(otp_provider="twilio", environment="test")
    p_twilio = get_otp_provider(s_twilio)
    assert isinstance(p_twilio, TwilioOTPProvider)

    s_fast = Settings(otp_provider="fast2sms", environment="test")
    p_fast = get_otp_provider(s_fast)
    assert isinstance(p_fast, Fast2SMSOTPProvider)

    s_prod = Settings(otp_provider="sms", environment="test")
    p_prod = get_otp_provider(s_prod)
    assert isinstance(p_prod, ProductionSMSOTPProvider)


def test_otp_provider_missing_credentials(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    p = AWSSNSOTPProvider()
    with pytest.raises(OTPDeliveryError) as exc_info:
        p.deliver(phone_number="+919876543210", code="123456")
    assert "PROVIDER-DEPENDENT" in str(exc_info.value)


def test_notification_provider_factory():
    s_smtp = Settings(email_provider="smtp", environment="test")
    p_smtp = get_provider(NotificationChannel.EMAIL, s_smtp)
    assert isinstance(p_smtp, SMTPEmailProvider)

    s_sns = Settings(sms_provider="aws_sns", environment="test")
    p_sns = get_provider(NotificationChannel.SMS, s_sns)
    assert isinstance(p_sns, AWSSNSNotificationProvider)


def test_notification_missing_credentials(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    p = AWSSESEmailProvider()
    msg = OutboundMessage(
        recipient="test@example.com",
        title="Test",
        body="Hello",
        channel=NotificationChannel.EMAIL,
    )
    res = p.send(msg)
    assert not res.success
    assert "PROVIDER-DEPENDENT" in (res.detail or "")


def test_submission_provider_factory():
    s_state = Settings(submission_provider="state_api", environment="test")
    p_state = get_submission_provider(s_state)
    assert isinstance(p_state, StatePortalApiSubmissionProvider)

    s_digi = Settings(submission_provider="digilocker", environment="test")
    p_digi = get_submission_provider(s_digi)
    assert isinstance(p_digi, DigiLockerSubmissionProvider)


def test_submission_missing_credentials(monkeypatch):
    monkeypatch.delenv("GOVT_PORTAL_API_URL", raising=False)
    monkeypatch.delenv("GOVT_PORTAL_API_KEY", raising=False)
    p = StatePortalApiSubmissionProvider()
    with pytest.raises(SubmissionProviderUnavailableError) as exc_info:
        p.submit_application(application_number="CL-2026-12345678", payload={})
    assert "PROVIDER-DEPENDENT" in str(exc_info.value)


def test_llm_provider_factory():
    s_openai = Settings(llm_provider="openai", environment="test")
    p_openai = get_llm_provider(s_openai)
    assert isinstance(p_openai, OpenAILLMProvider)

    s_anthropic = Settings(llm_provider="anthropic", environment="test")
    p_anthropic = get_llm_provider(s_anthropic)
    assert isinstance(p_anthropic, AnthropicLLMProvider)

    s_bedrock = Settings(llm_provider="aws_bedrock", environment="test")
    p_bedrock = get_llm_provider(s_bedrock)
    assert isinstance(p_bedrock, AWSBedrockLLMProvider)

    s_ollama = Settings(llm_provider="ollama", environment="test")
    p_ollama = get_llm_provider(s_ollama)
    assert isinstance(p_ollama, OllamaLLMProvider)


def test_llm_missing_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    p = OpenAILLMProvider()
    with pytest.raises(LLMError) as exc_info:
        p.generate("Tell me a story.")
    assert "PROVIDER-DEPENDENT" in str(exc_info.value)


def test_ocr_provider_factory():
    s_tess = Settings(ocr_provider="tesseract", environment="test")
    p_tess = get_ocr_provider(s_tess)
    assert isinstance(p_tess, TesseractOCRProvider)

    s_text = Settings(ocr_provider="aws_textract", environment="test")
    p_text = get_ocr_provider(s_text)
    assert isinstance(p_text, AWSTextractOCRProvider)


def test_ocr_missing_credentials(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    p = AWSTextractOCRProvider()
    with pytest.raises(OCRUnavailableError) as exc_info:
        p.extract_text(b"fake image bytes", "image/png")
    assert "PROVIDER-DEPENDENT" in str(exc_info.value)



def test_production_config_validation_rejects_test_providers():
    s = Settings(
        environment="production",
        jwt_secret_key="a-very-long-production-secure-jwt-secret-key-000000000",
        cors_origins_raw="https://civiclens.gov.in",
        storage_provider="s3",
        ocr_provider="test",
        submission_provider="mock",
        otp_provider="test",
        email_provider="test",
        sms_provider="test",
        push_provider="test",
        llm_provider="test",
        embedding_provider="test",
    )
    with pytest.raises(ValueError) as exc_info:
        s.validate_production_config()
    msg = str(exc_info.value)
    assert "OCR_PROVIDER='test'" in msg
    assert "SUBMISSION_PROVIDER='mock'" in msg
    assert "OTP_PROVIDER='test'" in msg
    assert "EMAIL_PROVIDER='test'" in msg
    assert "SMS_PROVIDER='test'" in msg
    assert "PUSH_PROVIDER='test'" in msg
    assert "LLM_PROVIDER='test'" in msg
