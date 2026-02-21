the project and draft work is going on so read later


.
.
.

.
..
.....





















...
.
.

..

'
'
'
'
'
'
'
'
'



















# 🔔 Notification Microservice — Payroll System

An **event-driven, production-grade Notification Microservice** built using **FastAPI**, **RabbitMQ**, and **PostgreSQL**.
This service asynchronously processes payroll events and delivers notifications through Email and SMS channels while maintaining complete audit tracking and retry handling.

---

## 🏗️ System Architecture

```
Payroll System
      ↓
RabbitMQ Broker (topic exchange: payroll_events)
      ↓
Notification Consumer (Async aio-pika)
      ↓
Template Processor (Jinja2 Rendering)
      ↓
Channel Service
   ├── Email (SMTP)
   └── SMS (Mock Provider)
      ↓
PostgreSQL Audit Database
   ├── notifications
   └── notification_logs
```

---

## ⚙️ Tech Stack

| Layer     | Technology                          |
| --------- | ----------------------------------- |
| Framework | FastAPI (Python 3.11+)              |
| Messaging | RabbitMQ + aio-pika                 |
| Database  | PostgreSQL + SQLAlchemy 2.0 (Async) |
| Migration | Alembic                             |
| Email     | aiosmtplib (SMTP)                   |
| SMS       | Mock Provider (Twilio/MSG91 ready)  |
| Templates | Jinja2                              |
| Logging   | structlog (JSON structured logging) |
| Testing   | pytest + pytest-asyncio             |

---

## 📁 Project Structure

```
notification_service/
│
├── app/
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── logging.py
│   ├── consumers/
│   │   └── payroll_consumer.py
│   ├── services/
│   │   ├── notification_service.py
│   │   └── retry_service.py
│   ├── channels/
│   │   ├── email_service.py
│   │   └── sms_service.py
│   ├── templates/
│   │   ├── message_templates.py
│   │   └── renderer.py
│   ├── models/
│   │   └── notification.py
│   ├── schemas/
│   │   └── events.py
│   ├── db/
│   │   └── base.py
│   ├── security/
│   │   └── validator.py
│   └── api/
│       └── routes.py
│
├── migrations/
├── tests/
├── requirements.txt
├── alembic.ini
└── README.md
```

---

## 📢 Supported Payroll Events

| Event              | Channel | Description                  |
| ------------------ | ------- | ---------------------------- |
| SalaryCredited     | SMS     | Salary credited notification |
| PayslipGenerated   | Email   | Payslip with attachment      |
| BonusCredited      | SMS     | Bonus payment alert          |
| OvertimeCalculated | Email   | Overtime report              |
| BankDetailsUpdated | SMS     | Bank account update alert    |

---

## 🚀 Setup & Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/3deiva/Notification_microservice.git
cd notification_service
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables

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

---

### 4️⃣ Run Database Migrations

```bash
alembic upgrade head
```

---

### 5️⃣ Start Notification Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Service runs at:

```
http://localhost:8000
```

Swagger Docs:

```
http://localhost:8000/docs
```

---

## 🔌 REST API

### Health Check

**GET /health**

```json
{
  "status": "UP",
  "service": "notification-service"
}
```

---

### Fetch Notifications

**GET /notifications/{employee_id}**

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

---

## 📨 Event Message Format (RabbitMQ)

Messages published to `payroll_events` exchange:

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
  "payload": {}
}
```

---

## 🔁 Retry & Failure Handling

- Maximum retries: **3**
- Backoff strategy: **Exponential (1s → 2s → 4s)**
- Dead Letter Queue: `notification_dlq`
- All attempts logged in `notification_logs`

---

## 🧪 Running Tests

```bash
pytest -v
```

Tests run using an in-memory SQLite database.

---

## 🔐 Security Features

- Event authentication via `auth_token`
- Sensitive data masked in logs
- No financial data persistence
- Immutable audit logging

---

## 📱 SMS Production Integration

Replace mock provider:

```python
from twilio.rest import Client

client = Client(TWILIO_SID, TWILIO_TOKEN)
client.messages.create(
    body=message,
    from_="+1XXXX",
    to=phone
)
```

---

## 📈 Key Engineering Concepts

- Event-Driven Architecture
- Asynchronous Processing
- Message Queue Decoupling
- Retry + Dead Letter Queues
- Structured Logging
- Clean Service Layer Design
- Production-ready Microservice Pattern

---

## 👨‍💻 Author

**Deiva Raja B**
IT Engineering Student | Backend & System Design Enthusiast

GitHub: https://github.com/3deiva

---

## 📄 License

This project is created for educational and system design demonstration purposes.
