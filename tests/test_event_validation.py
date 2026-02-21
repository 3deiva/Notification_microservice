import pytest
from pydantic import ValidationError
from app.schemas.events import BaseEvent, SalaryCreditedPayload, PayslipGeneratedPayload


VALID_BASE = {
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


def test_valid_base_event():
    event = BaseEvent(**VALID_BASE)
    assert event.event_id == "evt-1001"
    assert event.employee.employee_id == "EMP001"


def test_missing_auth_token_raises():
    data = {**VALID_BASE, "auth_token": ""}
    with pytest.raises(ValidationError):
        BaseEvent(**data)


def test_missing_event_type_raises():
    data = {k: v for k, v in VALID_BASE.items() if k != "event_type"}
    with pytest.raises(ValidationError):
        BaseEvent(**data)


def test_salary_credited_payload_valid():
    payload = SalaryCreditedPayload(
        month="February",
        year=2026,
        net_salary=45000,
        currency="INR",
        transaction_reference="TXN123",
    )
    assert payload.net_salary == 45000


def test_payslip_payload_valid():
    payload = PayslipGeneratedPayload(
        month="February",
        year=2026,
        gross_salary=52000,
        deductions=7000,
        net_salary=45000,
        payslip_pdf_url="https://example.com/payslip.pdf",
    )
    assert payload.payslip_pdf_url.startswith("https://")


def test_payslip_payload_missing_url_raises():
    with pytest.raises(ValidationError):
        PayslipGeneratedPayload(
            month="February",
            year=2026,
            gross_salary=52000,
            deductions=7000,
            net_salary=45000,
        )
