# 🔔 Notification Microservice — Payroll System

An **event-driven, production-grade Notification Microservice** built with **FastAPI**, **RabbitMQ**, and **PostgreSQL**.

---

## Architecture

```
Payroll System
      ↓
   RabbitMQ Broker  (topic exchange: payroll_events)
      ↓
Notification Consumer  (aio-pika async consumer)
      ↓
Template Processor  (Jinja2 rendering)
      ↓
Channel Service  (Email via SMTP / SMS via Mock Provider)
      ↓
PostgreSQL Audit Database  (notifications + notification_logs)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.11+) |
| Messaging | RabbitMQ + aio-pika |
| Database | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic |
| Email | aiosmtplib (SMTP) |
| SMS | Mock provider (replace with Twilio/MSG91) |
| Templates | Jinja2 |
| Logging | structlog (JSON structured logs) |
| Testing | pytest + pytest-asyncio |

---

## Project Structure

```
notification_service/
│
├── app/
│   ├── main.py                    # FastAPI app, lifespan hooks
│   ├── config/
│   │   ├── settings.py            # Pydantic settings (env-based config)
│   │   └── logging.py             # Structured logging setup
│   ├── consumers/
│   │   └── payroll_consumer.py    # RabbitMQ async consumer
│   ├── services/
│   │   ├── notification_service.py  # Core orchestration logic
│   │   └── retry_service.py         # Exponential backoff + DLQ routing
│   ├── channels/
│   │   ├── email_service.py       # SMTP email with attachment download
│   │   └── sms_service.py         # SMS mock provider
│   ├── templates/
│   │   ├── message_templates.py   # Template strings per event type
│   │   └── renderer.py            # Jinja2 rendering engine
│   ├── models/
│   │   └── notification.py        # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── events.py              # Pydantic validation schemas
│   ├── db/
│   │   └── base.py                # Async engine, session factory
│   ├── security/
│   │   └── validator.py           # Auth token + data masking
│   └── api/
│       └── routes.py              # REST API routes
│
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
├── tests/
│   ├── conftest.py
│   ├── test_event_validation.py
│   ├── test_notification_service.py
│   └── test_retry.py
├── requirements.txt
├── alembic.ini
└── README.md
```

---

## Supported Events

| Event | Channel | Trigger |
|-------|---------|---------|
| `SalaryCredited` | SMS | Salary credited to bank |
| `PayslipGenerated` | Email + Attachment | Monthly payslip ready |
| `BonusCredited` | SMS | Bonus payment credited |
| `OvertimeCalculated` | Email + Attachment | Overtime report ready |
| `BankDetailsUpdated` | SMS | Bank account changed |

---

## Setup & Installation

### 1. Install dependencies

```bash
cd notification_service
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notifications
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=yourpassword
SMTP_FROM_EMAIL=noreply@payroll.com
AUTH_TOKEN=secure-token
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## REST API

### GET /health

```json
{
  "status": "UP",
  "service": "notification-service"
}
```

### GET /notifications/{employee_id}

```json
[
  {
    "event_type": "SalaryCredited",
    "channel": "SMS",
    "status": "SENT",
    "timestamp": "2026-02-28T10:15:00Z"
  }
]
```

Swagger docs: `http://localhost:8000/docs`

---

## Event Input Format (RabbitMQ)

All messages published to the `payroll_events` exchange must follow:

```json
{
  "event_id": "evt-1001",
  "event_type": "SalaryCredited",
  "timestamp": "2026-02-28T10:15:00Z",
  "auth_token": "secure-token",
  "employee": {
    "employee_id": "EMP001",
    "name": "Arun Kumar",
    "phone": "9876543210"
  },
  "payload": { ... }
}
```

---

## Retry & Failure Handling

- **Max retries:** 3
- **Backoff:** Exponential (1s → 2s → 4s)
- **Dead Letter Queue:** `notification_dlq`
- All attempts logged to `notification_logs`

---

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database — no external services required.

---

## Security

- `auth_token` validated on every event
- Phone numbers and emails masked in logs
- No salary or bank data persisted beyond notification metadata
- Audit logs are immutable (append-only via ORM)

---

## SMS Production Setup

Replace `SMSService._call_provider` with your gateway of choice:

```python
# Example: Twilio
from twilio.rest import Client
client = Client(TWILIO_SID, TWILIO_TOKEN)
message = client.messages.create(body=message, from_="+1...", to=phone)
```
