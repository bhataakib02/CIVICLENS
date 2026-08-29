# CIVICLENS EXTERNAL PROVIDER MATRIX

**Version:** v1.0.0-rc.2  
**Date:** 2026-08-29  

---

## Provider Architecture & Activation Status

| Subsystem | Interface Name | Dev Provider | Production Provider | Credential Sources | Activation Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OTP Authentication** | `OTPProvider` | `DevOTPProvider` | `TwilioOTPProvider` / `Fast2SMSOTPProvider` | `OTP_API_KEY`, `OTP_SENDER_ID` | **PROVIDER-DEPENDENT** | Production adapter implemented; requires SMS provider key activation. |
| **Document OCR** | `OCRProvider` | `TestOCRProvider` | `AWSConsoleTextractProvider` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | **PROVIDER-DEPENDENT** | Multi-page PDF text extraction adapter complete; requires AWS Textract credentials. |
| **Document Malware Scan** | `MalwareScannerProvider` | `TestMalwareScanner` | `ClamAVScannerProvider` | `CLAMAV_HOST`, `CLAMAV_PORT` | **PROVIDER-DEPENDENT** | Socket streaming scanner ready; requires active ClamAV daemon. |
| **Government Portal** | `GovernmentSubmissionProvider` | `MockSubmissionProvider` | `StatePortalApiSubmissionProvider` | `GOVT_PORTAL_API_URL`, `GOVT_PORTAL_API_KEY` | **PROVIDER-DEPENDENT** | Complete API contract & idempotency header adapter built; external URL activation pending state portal credentials. |
| **Email Notifications** | `EmailProvider` | `TestEmailProvider` | `SendGridEmailProvider` | `SENDGRID_API_KEY`, `SENDER_EMAIL` | **PROVIDER-DEPENDENT** | Transactional email provider integrated; requires SendGrid token. |
| **SMS Notifications** | `SMSProvider` | `TestSMSProvider` | `TwilioSMSProvider` | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | **PROVIDER-DEPENDENT** | Production SMS adapter complete; requires Twilio account credentials. |
| **LLM & Embeddings** | `LLMProvider` / `EmbeddingProvider` | `TestLLMProvider` | `OpenAILLMProvider` / `GeminiLLMProvider` | `OPENAI_API_KEY` / `GEMINI_API_KEY` | **PROVIDER-DEPENDENT** | Vector store pgvector hybrid search active; external provider ready upon key entry. |

---

## Provider Fallback Guarantees

1. **Development Safety:** Non-production environments default to bundled test providers, ensuring local development and CI test suites run deterministically without external network access.
2. **Production Validation:** Setting `ENVIRONMENT=production` while keeping mock or test providers active triggers `validate_production_config()` at startup, causing the process to fail immediately with a clear error message.
