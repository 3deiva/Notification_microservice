from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Any
from datetime import datetime


class EmployeeInfo(BaseModel):
    employee_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    auth_token: str
    employee: EmployeeInfo
    payload: dict[str, Any]

    @field_validator("auth_token")
    @classmethod
    def auth_token_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("auth_token must not be empty")
        return v


class SalaryCreditedPayload(BaseModel):
    month: str
    year: int
    net_salary: float
    currency: str
    transaction_reference: str


class PayslipGeneratedPayload(BaseModel):
    month: str
    year: int
    gross_salary: float
    deductions: float
    net_salary: float
    payslip_pdf_url: str


class BonusCreditedPayload(BaseModel):
    bonus_type: str
    amount: float
    currency: str
    transaction_reference: str


class OvertimeCalculatedPayload(BaseModel):
    month: str
    year: int
    total_overtime_hours: float
    overtime_amount: float
    overtime_pdf_url: str


class BankDetailsUpdatedPayload(BaseModel):
    masked_account_number: str
    updated_at: datetime


class NotificationResponse(BaseModel):
    event_type: str
    channel: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    service: str
