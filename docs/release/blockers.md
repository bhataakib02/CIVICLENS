# CivicLens Blocker & External Activation Register

This register differentiates genuine engineering blockers from external credential activations, unverified cloud runtimes, and accepted architectural boundaries.

---

## 1. Engineering Blockers
- **Status**: 🟢 **ZERO ENGINEERING BLOCKERS**. All code, provider classes, error handling, idempotency, retry policies, CI pipelines, Terraform modules, and verification tools are implemented and tested.

---

## 2. External Credential Activations (PROVIDER-DEPENDENT)

When deploying to live staging or production environments, the following environment variables must be injected into AWS Secrets Manager or ECS environment configurations:

| Service Area | Provider | Required Environment Variables | Target Environment |
| --- | --- | --- | --- |
| **OTP Delivery** | AWS SNS / Twilio | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` / `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` | Production / Staging |
| **Email Delivery** | AWS SES / SendGrid | `AWS_ACCESS_KEY_ID`, `SES_FROM_EMAIL` / `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL` | Production / Staging |
| **Government Portal** | State Portal API | `GOVT_PORTAL_API_URL`, `GOVT_PORTAL_API_KEY` | Production / Staging |
| **AI LLM** | OpenAI / Bedrock | `OPENAI_API_KEY` / `AWS_ACCESS_KEY_ID`, `BEDROCK_MODEL_ID` | Production / Staging |
| **Cloud OCR** | AWS Textract | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Production / Staging |

---

## 3. Runtime Verification Status

| Environment | Infrastructure IaC | Code Implementation | Verification Tool | Verification Status |
| --- | --- | --- | --- | --- |
| **Local Dev / CI** | Docker Compose / Local | 🟢 100% Complete | Pytest, `verify_e2e*.py` | 🟢 Verified |
| **AWS Staging** | Terraform Staging Module | 🟢 100% Complete | `verify_aws_infrastructure.py` | 🟡 Cloud Execution Pending Credentials |
| **AWS Production** | Terraform Production Module | 🟢 100% Complete | `verify_aws_infrastructure.py` | 🟡 Cloud Execution Pending Credentials |
