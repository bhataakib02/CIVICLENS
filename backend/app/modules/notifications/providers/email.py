"""Email provider abstraction + NON_PRODUCTION console dev provider (prompt §13, §28).

ConsoleEmailProvider only logs a PII-safe line (never the body/recipient) and
returns SENT — never DELIVERED — because no external system confirmed receipt
(prompt §54). A real provider (SES/SendGrid/...) would be added here and
configured via EMAIL_PROVIDER; credentials come from the environment only.
"""
from __future__ import annotations

import uuid

from app.core.logging import get_logger
from app.models.enums import DeliveryErrorCode, NotificationChannel
from app.modules.notifications.providers.base import (
    DeliveryProvider,
    DeliveryResult,
    OutboundMessage,
)

logger = get_logger("civiclens.notifications.email")


def _looks_like_email(addr: str) -> bool:
    return "@" in addr and "." in addr.split("@")[-1] and len(addr) <= 320


class ConsoleEmailProvider(DeliveryProvider):
    """NON_PRODUCTION: logs a PII-safe line; does not send real email."""

    channel = NotificationChannel.EMAIL
    name = "console"
    non_production = True

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not message.recipient or not _looks_like_email(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=True, error_code=DeliveryErrorCode.INVALID_EMAIL,
            )
        # PII-safe: log only channel + title, never the body or address.
        logger.info("email_console_sent", extra={"title": message.title})
        return DeliveryResult(
            success=True, channel=self.channel, provider=self.name, non_production=True,
            provider_message_id=f"console-{uuid.uuid4().hex[:16]}",
            detail="NON_PRODUCTION console email; not delivered by a real provider.",
        )


class SMTPEmailProvider(DeliveryProvider):
    """Production Email delivery via SMTP."""

    channel = NotificationChannel.EMAIL
    name = "smtp"
    non_production = False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        import os
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not message.recipient or not _looks_like_email(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.INVALID_EMAIL,
            )

        host = os.getenv("SMTP_HOST", "localhost")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER", "")
        password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("SMTP_FROM", "noreply@civiclens.gov.in")

        if not host or (port != 25 and not user):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name, non_production=False,
                detail="SMTP credentials missing (SMTP_HOST, SMTP_USER, SMTP_PASSWORD). Activation is PROVIDER-DEPENDENT.",
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = message.recipient
            msg["Subject"] = message.title
            msg.attach(MIMEText(message.body, "plain"))

            with smtplib.SMTP(host, port, timeout=10.0) as server:
                if port == 587:
                    server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)

            msg_id = f"smtp-{uuid.uuid4().hex[:16]}"
            return DeliveryResult(
                success=True, channel=self.channel, provider=self.name,
                non_production=False, provider_message_id=msg_id, detail="SMTP email sent",
            )
        except Exception as exc:
            logger.error("SMTP delivery failed: %s", exc)
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.TRANSIENT_NETWORK_FAILURE, detail=str(exc),
            )


class AWSSESEmailProvider(DeliveryProvider):
    """Production Email delivery via AWS SES."""

    channel = NotificationChannel.EMAIL
    name = "aws_ses"
    non_production = False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        import os

        if not message.recipient or not _looks_like_email(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.INVALID_EMAIL,
            )

        region = os.getenv("AWS_REGION", "ap-south-1")
        from_email = os.getenv("SES_FROM_EMAIL", "noreply@civiclens.gov.in")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")

        if not access_key:
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name, non_production=False,
                detail="AWS SES credentials missing. Activation is PROVIDER-DEPENDENT.",
            )

        try:
            import boto3

            client = boto3.client("ses", region_name=region)
            resp = client.send_email(
                Source=from_email,
                Destination={"ToAddresses": [message.recipient]},
                Message={
                    "Subject": {"Data": message.title, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": message.body, "Charset": "UTF-8"}},
                },
            )
            msg_id = resp.get("MessageId", f"ses-{uuid.uuid4().hex[:16]}")
            return DeliveryResult(
                success=True, channel=self.channel, provider=self.name,
                non_production=False, provider_message_id=msg_id, detail="AWS SES email sent",
            )
        except Exception as exc:
            logger.error("AWS SES delivery failed: %s", exc)
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.TRANSIENT_NETWORK_FAILURE, detail=str(exc),
            )


class SendGridEmailProvider(DeliveryProvider):
    """Production Email delivery via SendGrid API."""

    channel = NotificationChannel.EMAIL
    name = "sendgrid"
    non_production = False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        import os

        if not message.recipient or not _looks_like_email(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.INVALID_EMAIL,
            )

        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@civiclens.gov.in")

        if not api_key:
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name, non_production=False,
                detail="SendGrid API key missing. Activation is PROVIDER-DEPENDENT.",
            )

        try:
            import httpx

            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "personalizations": [{"to": [{"email": message.recipient}]}],
                "from": {"email": from_email},
                "subject": message.title,
                "content": [{"type": "text/plain", "value": message.body}],
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()

            return DeliveryResult(
                success=True, channel=self.channel, provider=self.name,
                non_production=False, provider_message_id=f"sg-{uuid.uuid4().hex[:16]}", detail="SendGrid email sent",
            )
        except Exception as exc:
            logger.error("SendGrid email delivery failed: %s", exc)
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.TRANSIENT_NETWORK_FAILURE, detail=str(exc),
            )

