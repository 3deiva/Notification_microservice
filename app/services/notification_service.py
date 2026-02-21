import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.channels.email_service import EmailService
from app.channels.sms_service import SMSService
from app.config import settings
from app.config.logging import get_logger
from app.models.notification import Notification, NotificationLog
from app.schemas.events import (
    BaseEvent, SalaryCreditedPayload, PayslipGeneratedPayload,
    BonusCreditedPayload, OvertimeCalculatedPayload, BankDetailsUpdatedPayload,
)
from app.security.validator import SecurityValidator
from app.templates.renderer import TemplateProcessor

logger = get_logger(__name__)

PAYLOAD_SCHEMAS = {
    "SalaryCredited": SalaryCreditedPayload,
    "PayslipGenerated": PayslipGeneratedPayload,
    "BonusCredited": BonusCreditedPayload,
    "OvertimeCalculated": OvertimeCalculatedPayload,
    "BankDetailsUpdated": BankDetailsUpdatedPayload,
}


class NotificationService:
    """Orchestrates the full notification lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_event(self, raw_data: dict[str, Any]) -> None:
        logger.info("event_received", event_id=raw_data.get("event_id"), event_type=raw_data.get("event_type"))

        # 1. Parse and validate base event
        event = BaseEvent(**raw_data)

        # 2. Security check
        if not SecurityValidator.validate_token(event.auth_token):
            raise PermissionError(f"Invalid auth_token for event {event.event_id}")

        # 3. Validate payload
        payload_schema = PAYLOAD_SCHEMAS.get(event.event_type)
        if not payload_schema:
            raise ValueError(f"Unknown event_type: {event.event_type}")

        validated_payload = payload_schema(**event.payload)
        logger.info("event_validated", event_id=event.event_id, event_type=event.event_type)

        # 4. Render template
        context = {
            "name": event.employee.name,
            **validated_payload.model_dump(),
        }
        rendered = TemplateProcessor.render(event.event_type, context)
        channel = rendered["channel"].upper()

        # 5. Create notification record
        notification = Notification(
            employee_id=event.employee.employee_id,
            event_type=event.event_type,
            channel_type=channel,
            status="PENDING",
        )
        self.db.add(notification)
        await self.db.flush()

        # 6. Send via appropriate channel
        try:
            result = await self._dispatch(event, rendered, channel, validated_payload)
            notification.status = "SENT"
            await self._log(notification.id, response_message=result["message"])
            logger.info("notification_sent", notification_id=str(notification.id), channel=channel)
        except Exception as e:
            notification.status = "FAILED"
            await self._log(notification.id, error_message=str(e))
            logger.error("notification_failed", notification_id=str(notification.id), error=str(e))
            raise

        await self.db.commit()

    async def _dispatch(
        self,
        event: BaseEvent,
        rendered: dict[str, str],
        channel: str,
        payload: Any,
    ) -> dict:
        if channel == "SMS":
            phone = event.employee.phone
            if not phone:
                raise ValueError(f"No phone number for employee {event.employee.employee_id}")
            return await SMSService.send(phone, rendered["sms"])

        elif channel == "EMAIL":
            email = event.employee.email
            if not email:
                raise ValueError(f"No email for employee {event.employee.employee_id}")

            attachment_url = getattr(payload, "payslip_pdf_url", None) or getattr(payload, "overtime_pdf_url", None)
            return await EmailService.send(
                to_email=email,
                subject=rendered["subject"],
                body=rendered["body"],
                attachment_url=attachment_url,
            )

        raise ValueError(f"Unsupported channel: {channel}")

    async def _log(self, notification_id: uuid.UUID, response_message: str = None, error_message: str = None) -> None:
        log = NotificationLog(
            notification_id=notification_id,
            response_message=response_message,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )
        self.db.add(log)

    async def get_notifications_by_employee(self, employee_id: str) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.employee_id == employee_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()
