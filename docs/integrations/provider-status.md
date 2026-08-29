# CivicLens Provider Integration Status Matrix

This document records the exact implementation and runtime status of every provider interface across the CivicLens platform.

---

## Provider Status Register

| Category | Interface | Implementation Class | Runtime Status | Credentials Required | Fallback / Dev Mode |
| --- | --- | --- | --- | --- | --- |
| **OTP Delivery** | `OTPProvider` | `AWSSNSOTPProvider` / `TwilioOTPProvider` / `Fast2SMSOTPProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `AWS_ACCESS_KEY_ID`, `TWILIO_ACCOUNT_SID`, `FAST2SMS_API_KEY` | `TestOTPProvider` (Dev/Test only) |
| **Email Notifications** | `DeliveryProvider` | `SMTPEmailProvider` / `AWSSESEmailProvider` / `SendGridEmailProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `SMTP_USER`, `SES_FROM_EMAIL`, `SENDGRID_API_KEY` | `ConsoleEmailProvider` (Dev/Test only) |
| **SMS Notifications** | `DeliveryProvider` | `AWSSNSNotificationProvider` / `TwilioSMSNotificationProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `AWS_ACCESS_KEY_ID`, `TWILIO_ACCOUNT_SID` | `FakeSMSProvider` (Dev/Test only) |
| **Push Notifications** | `DeliveryProvider` | `FCMPushNotificationProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `FCM_SERVER_KEY` | `FakePushProvider` (Dev/Test only) |
| **Government Portal API** | `GovernmentSubmissionProvider` | `StatePortalApiSubmissionProvider` / `DigiLockerSubmissionProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `GOVT_PORTAL_API_URL`, `GOVT_PORTAL_API_KEY`, `DIGILOCKER_CLIENT_ID` | `MockSubmissionProvider` (Dev/Test only) |
| **LLM Reasoning** | `LLMProvider` | `OpenAILLMProvider` / `AnthropicLLMProvider` / `AWSBedrockLLMProvider` / `OllamaLLMProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_ACCESS_KEY_ID` | `DeterministicGroundedTestProvider` (Dev/Test only) |
| **Document OCR** | `OCRProvider` | `TesseractOCRProvider` / `AWSTextractOCRProvider` / `PdfTextOCRProvider` | 🟢 COMPLETE (`PROVIDER-DEPENDENT`) | `AWS_ACCESS_KEY_ID` (for Textract); Tesseract binary (for Tesseract) | `TestOCRProvider` / `PdfTextOCRProvider` |
| **Storage** | `StorageProvider` | `S3StorageProvider` / `LocalStorageProvider` | 🟢 COMPLETE | `S3_BUCKET`, `AWS_REGION` | `LocalStorageProvider` (Dev/Test only) |

---

## Classification Definitions

- **COMPLETE**: Interface, error handling, timeouts, idempotency keys, logging, and production settings validation are fully implemented in code.
- **PROVIDER-DEPENDENT**: Production activation requires injecting external vendor API keys/credentials into the runtime environment.
- **DEV/TEST ONLY**: Deterministic mock implementation used automatically when `ENVIRONMENT != production`.
