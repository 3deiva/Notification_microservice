import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from app.services.notification_service import NotificationService


SALARY_EVENT = {
    "event_id": "evt-1001",
    "event_type": "SalaryCredited",
    "timestamp": "2026-02-28T10:15:00Z",
    "auth_token": "secure-token",
    "employee": {
        "employee_id": "EMP001",
        "name": "Arun Kumar",
        "phone": "9876543210",
    },
    "payload": {
        "month": "February",
        "year": 2026,
        "net_salary": 45000,
        "currency": "INR",
        "transaction_reference": "TXN9845123",
    },
}

PAYSLIP_EVENT = {
    "event_id": "evt-1002",
    "event_type": "PayslipGenerated",
    "timestamp": "2026-02-28T09:00:00Z",
    "auth_token": "secure-token",
    "employee": {
        "employee_id": "EMP001",
        "name": "Arun Kumar",
        "email": "arun@example.com",
    },
    "payload": {
        "month": "February",
        "year": 2026,
        "gross_salary": 52000,
        "deductions": 7000,
        "net_salary": 45000,
        "payslip_pdf_url": "https://example.com/payslip.pdf",
    },
}


@pytest.mark.asyncio
async def test_salary_credited_sends_sms(db_session):
    with patch("app.services.notification_service.SMSService.send", new_callable=AsyncMock) as mock_sms:
        mock_sms.return_value = {"status": "SENT", "message": "SMS sent"}
        service = NotificationService(db_session)
        await service.process_event(SALARY_EVENT)
        mock_sms.assert_called_once()
        call_args = mock_sms.call_args
        assert "9876543210" in call_args[1]["phone"] or "9876543210" == call_args[0][0]


@pytest.mark.asyncio
async def test_payslip_generated_sends_email(db_session):
    with patch("app.services.notification_service.EmailService.send", new_callable=AsyncMock) as mock_email:
        mock_email.return_value = {"status": "SENT", "message": "Email sent"}
        service = NotificationService(db_session)
        await service.process_event(PAYSLIP_EVENT)
        mock_email.assert_called_once()
        kwargs = mock_email.call_args[1]
        assert kwargs["to_email"] == "arun@example.com"
        assert "February" in kwargs["subject"]


@pytest.mark.asyncio
async def test_invalid_auth_token_raises(db_session):
    event = {**SALARY_EVENT, "auth_token": "wrong-token"}
    service = NotificationService(db_session)
    with pytest.raises(PermissionError):
        await service.process_event(event)


@pytest.mark.asyncio
async def test_unknown_event_type_raises(db_session):
    event = {**SALARY_EVENT, "event_type": "UnknownEvent"}
    service = NotificationService(db_session)
    with pytest.raises(ValueError, match="Unknown event_type"):
        await service.process_event(event)


@pytest.mark.asyncio
async def test_notification_recorded_in_db(db_session):
    with patch("app.services.notification_service.SMSService.send", new_callable=AsyncMock) as mock_sms:
        mock_sms.return_value = {"status": "SENT", "message": "SMS sent"}
        service = NotificationService(db_session)
        await service.process_event(SALARY_EVENT)
        notifications = await service.get_notifications_by_employee("EMP001")
        assert len(notifications) == 1
        assert notifications[0].status == "SENT"
        assert notifications[0].event_type == "SalaryCredited"
