import aiosmtplib
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from app.config import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Sends email notifications via SMTP."""

    @staticmethod
    async def _download_attachment(url: str) -> Optional[bytes]:
        """Download PDF attachment from URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.warning("attachment_download_failed", url=url, error=str(e))
            return None

    @classmethod
    async def send(
        cls,
        to_email: str,
        subject: str,
        body: str,
        attachment_url: Optional[str] = None,
        attachment_filename: Optional[str] = "document.pdf",
    ) -> dict:
        """Send email, optionally with attachment. Returns result dict."""
        msg = MIMEMultipart()
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachment_url:
            data = await cls._download_attachment(attachment_url)
            if data:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{attachment_filename}"')
                msg.attach(part)
            else:
                logger.warning("email_sent_without_attachment", to=to_email)

        try:
            if not settings.SMTP_USERNAME:
                # Mock mode — log and return success without actual SMTP
                logger.info(
                    "email_mock_sent",
                    to=to_email,
                    subject=subject,
                    body_preview=body[:80],
                )
                return {"status": "SENT", "message": f"[MOCK] Email sent to {to_email}"}

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=False,
                start_tls=True,
            )
            logger.info("email_sent", to=to_email, subject=subject)
            return {"status": "SENT", "message": f"Email sent to {to_email}"}

        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            raise
