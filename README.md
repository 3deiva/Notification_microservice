# 🔔 Notification Microservice — Payroll System

> **TEAM A² - (AGILE × ALLIANCE)**
> 
> A Square (A²) represents the combination of Agile methodology and strong team alliance. It symbolizes how collaborative teamwork amplifies Agile practices to deliver efficient, iterative, and high-quality solutions.

---

## 📋 Table of Contents

1. [Problem Statement & Our Interpretation](#1-problem-statement--our-interpretation)
2. [Payroll Context — What We Inferred](#2-payroll-context--what-we-inferred)
3. [Why Notification as a Microservice](#3-why-notification-as-a-microservice)
4. [Scrum Team & Roles](#4-scrum-team--roles)
5. [Sprint Zero — Discovery & Planning](#5-sprint-zero--discovery--planning)
6. [Technology Stack — Why We Chose Each Tool](#6-technology-stack--why-we-chose-each-tool)
7. [Sprint 1 — Core Consumer & Email Notification](#7-sprint-1--core-consumer--email-notification)
8. [Sprint 2 — SMS, Attachments & All Five Events](#8-sprint-2--sms-attachments--all-five-events)
9. [Sprint 3 — Retry, Dead Letter Queue & Security](#9-sprint-3--retry-dead-letter-queue--security)
10. [System Architecture](#10-system-architecture)
11. [Project Structure](#11-project-structure)
12. [Event Input Contracts](#12-event-input-contracts)
13. [Database Design](#13-database-design)
14. [REST API Reference](#14-rest-api-reference)
15. [Testing](#15-testing)
16. [Setup & Running the Project](#16-setup--running-the-project)
17. [Live Demo — Testing All Five Events](#17-live-demo--testing-all-five-events)
18. [What We Have Not Implemented — Future Scope](#18-what-we-have-not-implemented--future-scope)

---

## 1. Problem Statement & Our Interpretation

### Given Problem Statement

> *"Build a Notification System for a Payroll System"*

That was the complete problem statement. No additional constraints, no technical specifications, no event definitions — just this single sentence.

### How We Approached It

As a Scrum team, we treated this deliberately minimal problem statement as a **product discovery opportunity** — exactly what Sprint Zero is designed for. Rather than jumping into code, we asked ourselves the same questions a real Business Analyst would ask a client:

- What payroll events need notifications?
- Who receives the notifications?
- Through which channels?
- What data does each notification carry?
- What are the security boundaries?
- Where does payroll responsibility end and notification responsibility begin?

This structured thinking — before writing a single line of code — is what separates a professional delivery from a rushed submission. Our README reflects that process transparently because the README is our primary communication with the judges, and we want every decision to be traceable to a business reason.

---

## 2. Payroll Context — What We Inferred

Since the problem statement gave us no payroll context, our **Business Analyst** led a structured discovery session. We defined a realistic payroll environment before designing the notification system — because you cannot design a notification system without understanding what triggers the notifications.

### Business Environment Assumed

We assumed the payroll system belongs to a **mid-sized manufacturing organization** with three employee categories:

- **Factory Workers** — shift-based, overtime-eligible, may not have reliable email access, primarily receive SMS
- **Supervisors** — performance incentive-based, receive both SMS and email
- **Administrative Staff** — fixed salary structure, email-primary communication

This assumption directly influenced our channel design: we support both **Email and SMS** because different employee types have different communication preferences and access levels. A factory worker on the shop floor is more likely to see an SMS than to open their email.

### What the Payroll System Does (Outside Our Scope)

We clearly defined the payroll system's responsibilities so we could draw a hard boundary:

| Payroll Responsibility | Notification Responsibility |
|------------------------|----------------------------|
| Calculate gross salary | ❌ Not our concern |
| Apply PF, tax deductions | ❌ Not our concern |
| Compute net salary | ❌ Not our concern |
| Process bank transfer | ❌ Not our concern |
| Generate payslip PDF | ❌ Not our concern |
| Generate overtime PDF | ❌ Not our concern |
| **Publish events to RabbitMQ** | ✅ We consume these |
| **Send SMS to employee** | ✅ We do this |
| **Send email with payslip** | ✅ We do this |
| **Log delivery status** | ✅ We do this |

This separation is not just good design — it is the definition of a microservice.

### Payroll Processing Workflow (Our Assumed Flow)

We mapped the payroll cycle to identify exactly where notifications are needed:

```
1. Attendance Finalized
2. Salary Computed (gross → deductions → net)
3. Bank Transfer Processed          → triggers SalaryCredited event
4. Payslip PDF Generated            → triggers PayslipGenerated event
5. Overtime Calculated & Documented → triggers OvertimeCalculated event
6. Bonus Computed & Credited        → triggers BonusCredited event
7. Employee Updates Bank Details    → triggers BankDetailsUpdated event
```

Each of these steps is a natural communication trigger. An employee needs to know when their money moves, when their documents are ready, and when their account details change.

### Derived Payroll Events

From the workflow above, we defined **five payroll events** the notification service must handle:

| Event | Trigger | Channel |
|-------|---------|---------|
| `SalaryCredited` | Bank transfer complete | SMS |
| `PayslipGenerated` | PDF ready | Email + Attachment |
| `BonusCredited` | Bonus disbursed | SMS |
| `OvertimeCalculated` | Overtime report ready | Email + Attachment |
| `BankDetailsUpdated` | Account changed | SMS (security alert) |

### Security & Data Boundary

Because payroll data is highly sensitive, we established strict data rules before implementation:

- The notification service **never stores salary computation details**
- The notification service **never accesses the payroll database**
- We store only **delivery metadata** — who was notified, when, through which channel, success or failure
- Phone numbers and emails are **masked in logs** — `******3210` not `9876543210`
- Payslip PDFs are downloaded temporarily for email attachment and **not stored permanently**

This ensures our service respects financial data sensitivity requirements even without an explicit compliance brief.

---

## 3. Why Notification as a Microservice

When the problem said "build a notification system for a payroll system," we had two architectural options:

**Option A** — Build notification as a module inside the payroll system
**Option B** — Build notification as an independent microservice

We chose Option B immediately, and here is exactly why.

### Reason 1 — Non-Blocking Payroll Processing

If notification were inside payroll, a slow SMTP server or SMS gateway outage would **delay salary processing**. That is unacceptable — salary must be credited on time regardless of communication failures. As a separate service connected via a message queue, a notification failure never affects the payroll engine.

### Reason 2 — Independent Scalability

On salary credit day (typically month-end), thousands of notifications fire simultaneously. As a microservice, we can **scale the notification service independently** — spinning up more consumer instances — without touching or risking the payroll infrastructure.

### Reason 3 — Fault Isolation

If the notification service crashes, **payroll continues to run**. Events queue up in RabbitMQ and are processed when the service recovers — no data loss, no payroll disruption.

### Reason 4 — Channel Flexibility

Today we support Email and SMS. Tomorrow we may add WhatsApp, push notifications, or in-app alerts. As a microservice, we **add new channels without modifying payroll** at all. The payroll system simply publishes an event and moves on.

### Reason 5 — Reusability

The same notification service can serve HR systems, leave management, expense approval — any system that needs to communicate with employees. Building it as a microservice makes it a **shared organizational capability** rather than a module buried inside one system.

### Reason 6 — Clean Data Boundaries

Payroll has confidential computation logic. Notification has delivery logic. Mixing them in one codebase is a security and compliance risk. Microservice separation enforces data boundaries at the architectural level.

---

## 4. Scrum Team & Roles

We operated as a proper Scrum team with defined roles and responsibilities throughout the project.

### 👤 Scrum Master
Facilitated all Scrum ceremonies — Sprint Zero, Sprint Planning, Sprint Reviews, and Retrospectives. Ensured the team followed Agile principles, removed blockers, and kept sprints focused. The Scrum Master also enforced the Definition of Done for each user story so that "done" meant truly done — not just coded, but tested, documented, and logged.

### 👤 Business Analyst
Led the payroll context discovery session. Translated the minimal problem statement into concrete user stories with acceptance criteria. Defined the event contracts, data schemas, and channel routing rules. Ensured the team understood business requirements before implementation started so no assumptions were baked silently into code.

### 👤 Developer
Implemented the entire technical solution — FastAPI application, RabbitMQ consumer, Email and SMS channels, database models, retry mechanism, security validation, Alembic migrations, and REST API. Made technology decisions guided by requirements defined by the Business Analyst and accepted by the Product Owner.

### 👤 Tester
Defined the test strategy, wrote test cases for each sprint, and verified that each user story met its acceptance criteria before marking it Done. Tested event validation, service orchestration behavior, retry logic, DLQ routing, and security validation.

---

## 5. Sprint Zero — Discovery & Planning

Sprint Zero was our most important phase. **No code was written.** Every decision made here shaped the entire implementation.

### Activity 1 — Domain Analysis

The Business Analyst ran a structured payroll domain analysis. The team discussed:

- What is a payroll system and how does the salary cycle work?
- What events naturally occur in a payroll workflow?
- Who needs to be notified and when?
- What information does each notification carry?
- What are the failure scenarios and how should we handle them?

This session produced the payroll context documented in Section 2. It took deliberate time — and saved far more time during implementation by eliminating ambiguity.

### Activity 2 — User Story Definition

The Product Owner wrote user stories in standard format. Each story was reviewed by the full team and estimated in story points.

---

**US-001 — Salary Credit SMS**
*As a factory worker, I want to receive an SMS when my salary is credited so that I am immediately informed without needing to check my bank app.*

Acceptance Criteria:
- SMS is sent within seconds of the `SalaryCredited` event being received
- SMS contains the month, net salary amount, and transaction reference number
- SMS is sent even if email is unavailable
- Delivery status is logged in the database

**Story Points: 3**

---

**US-002 — Payslip Email with Attachment**
*As an employee, I want to receive my payslip as an email attachment so that I have a professional document for my records.*

Acceptance Criteria:
- Email is sent when `PayslipGenerated` event is received
- Email subject clearly states the month and year
- Payslip PDF is downloaded from the provided URL and attached to the email
- If PDF download fails, email is still sent without attachment and failure is logged
- Delivery status is recorded in the database

**Story Points: 5**

---

**US-003 — Bonus Credit SMS**
*As a supervisor, I want to receive an SMS when my performance bonus is credited so that I am immediately aware of the disbursement.*

Acceptance Criteria:
- SMS sent on `BonusCredited` event
- SMS contains bonus type, credited amount, and transaction reference
- Delivery logged in database

**Story Points: 2**

---

**US-004 — Overtime Statement Email**
*As a factory worker, I want to receive my overtime breakdown by email so that I can verify my overtime hours and payment.*

Acceptance Criteria:
- Email sent on `OvertimeCalculated` event
- Overtime PDF downloaded and attached to the email
- Email body contains total overtime hours and overtime amount

**Story Points: 3**

---

**US-005 — Bank Details Security Alert**
*As an employee, I want to receive an SMS when my bank account details are changed so that I can immediately report unauthorized changes to HR.*

Acceptance Criteria:
- SMS sent immediately on `BankDetailsUpdated` event
- SMS contains masked account number (e.g., XXXX1234)
- SMS includes instruction to contact HR if the change was unauthorized

**Story Points: 2**

---

**US-006 — Notification History API**
*As a payroll administrator, I want to query notification history by employee ID so that I can verify delivery status and resolve employee disputes about missing notifications.*

Acceptance Criteria:
- REST API endpoint returns all notifications for a given employee ID
- Response includes event type, channel, status, and timestamp
- Returns an appropriate response when no notifications are found

**Story Points: 3**

---

**US-007 — Retry on Failure**
*As a system administrator, I want failed notifications to be retried automatically so that temporary gateway outages or network hiccups do not result in missed employee notifications.*

Acceptance Criteria:
- Maximum 3 retry attempts per failed notification
- Exponential backoff between retries — 1 second, 2 seconds, 4 seconds
- After 3 consecutive failures, message is moved to Dead Letter Queue for manual inspection
- Every retry attempt is logged with attempt number, delay, and error reason

**Story Points: 5**

---

**US-008 — Security Token Validation**
*As a security engineer, I want all incoming events to carry a valid authentication token so that only the authorized payroll system can trigger employee notifications.*

Acceptance Criteria:
- Events without a valid auth token are rejected immediately
- Rejection is logged with event ID and reason
- No notification is sent for events that fail token validation

**Story Points: 2**

---

### Activity 3 — Sprint Planning

After story definition, the Scrum Master facilitated sprint planning. Stories were distributed across three sprints based on dependencies and priority.

| Sprint | Stories | Focus |
|--------|---------|-------|
| Sprint 1 | US-001 (infra), US-002, US-006 | Core consumer, Email, History API |
| Sprint 2 | US-001 (complete), US-003, US-004, US-005 | SMS channel, all event types |
| Sprint 3 | US-007, US-008 | Retry, DLQ, Security validation |

**Total Story Points: 25**

### Activity 4 — Architecture Decision

The team evaluated two approaches for receiving payroll events:

| Option | Approach | Decision |
|--------|----------|----------|
| HTTP Polling | Notification calls payroll API to check for new events | ❌ Rejected — tight coupling, polling wastes resources |
| Message Queue | Payroll publishes events, notification consumes asynchronously | ✅ Chosen — decoupled, reliable, async |

**Decision: Event-Driven Architecture with RabbitMQ.**

Payroll publishes an event and moves on immediately. Notification processes independently at its own pace. No runtime dependency between the two services.

### Activity 5 — Event Contract Definition

The Business Analyst defined the JSON contract for all five events before Sprint 1 began. Every field was discussed — why it exists, what it contains, whether optional or required. These contracts were locked so the Developer had a clear interface and the Tester had a clear basis for validation tests.

### Activity 6 — Database Schema Design

The team agreed on a two-table schema:

- `notifications` — one record per notification, captures employee, event type, channel, and final status
- `notification_logs` — one record per delivery attempt, captures provider response or error message

This separation allows tracking both the overall notification outcome and detailed delivery attempt history independently — supporting both operational monitoring and compliance auditing.

### Activity 7 — Definition of Done

The team agreed on a Definition of Done applied to every user story before it could be marked complete:

- Code written and working against the event contract
- Unit tests passing for that story's functionality
- Database record created for every notification attempt
- Structured JSON logs produced for every significant action
- Swagger documentation reflects the endpoint behavior

---

## 6. Technology Stack — Why We Chose Each Tool

Every technology decision was made deliberately. Here is the full reasoning including cost, which was a primary consideration.

### Python 3.11 + FastAPI

**Why Python?** The team was most proficient in Python, which reduces implementation risk in a time-constrained delivery. Python also has excellent async support — critical for an event-driven system where we must process multiple events concurrently without blocking.

**Why FastAPI?** FastAPI is modern, high-performance, and generates **interactive Swagger documentation automatically** with zero additional effort. Since the judge evaluates via the README and a live demo, having working Swagger UI at `/docs` is a significant advantage. FastAPI also uses Pydantic for automatic request validation — our event schema validation was handled by the framework, not custom code, reducing bugs.

**Cost: Free and open source.**

### RabbitMQ

**Why RabbitMQ?** RabbitMQ is the industry-standard message broker for event-driven systems. It provides:
- **Topic exchanges** — route messages by pattern (`payroll.#` matches any payroll event)
- **Dead Letter Queues** — failed messages are not lost, they are routed to an inspection queue
- **Message durability** — messages survive broker restarts without loss
- **Acknowledgement-based delivery** — messages are not removed until processing is confirmed

We considered Redis Streams as an alternative but chose RabbitMQ because native Dead Letter Queue support was a core requirement (US-007). We rejected Kafka because it is designed for high-throughput streaming at massive scale and adds significant operational complexity that is not justified for our message volume.

**Cost: Free and open source.**

### aio-pika (Async RabbitMQ Client)

The standard `pika` library is synchronous. Since FastAPI is fully async, a synchronous RabbitMQ client would block the event loop and prevent parallel processing. `aio-pika` is the official async Python client for RabbitMQ — the only correct choice for our architecture.

**Cost: Free and open source.**

### PostgreSQL + SQLAlchemy 2.0 + Alembic

**Why PostgreSQL?** We needed a reliable relational database for audit logs. Notification history must be queryable, filterable, and immutable. PostgreSQL supports UUID primary keys natively, handles concurrent writes reliably, and is free.

**Why SQLAlchemy 2.0?** Writing raw SQL increases the risk of errors and makes the codebase harder to maintain. SQLAlchemy's async ORM provides type-safe database operations, handles connection pooling automatically, and integrates with Alembic for migrations.

**Why Alembic?** Database schema must evolve as the product evolves. Alembic provides version-controlled migrations so schema changes are tracked, reversible, and reproducible across environments — essential for any serious project.

**Cost: All free and open source.**

### Twilio (SMS Gateway)

**Why Twilio?** Twilio is the globally recognized standard for programmable SMS. For our use case:
- **Free trial** provides real SMS delivery to verified numbers — no cost for the demo
- Delivers SMS within seconds globally including India
- Simple Python SDK with clear error responses
- Provides delivery confirmation and message SID for audit logging

**Cost: Free trial sufficient for demo. ~₹1–2 per SMS in production.**

### Gmail SMTP (Email)

**Why Gmail SMTP?** Gmail SMTP is completely free, universally accessible, and requires zero account setup beyond an App Password. For a project of this scope, Gmail SMTP demonstrates real email delivery capability without the cost and approval process of paid services like SendGrid or AWS SES.

**Cost: Completely free.**

### Jinja2 (Message Templating)

Notification messages cannot be hardcoded. Each event type requires a different format, and message content varies per employee (name, amount, month, reference). Jinja2 allows defining message templates with placeholders and rendering them dynamically. This is the industry-standard approach used in production systems — the same engine that powers Django email templates.

**Cost: Free and open source.**

### structlog (Structured Logging)

Plain text logs like `print("SMS sent")` are useless in production. We needed **structured JSON logs** where every line contains event type, employee ID, notification ID, channel, timestamp, and outcome — so logs can be searched, filtered, and analyzed programmatically. structlog produces machine-readable JSON that works with any log aggregation platform.

**Cost: Free and open source.**

### pytest + pytest-asyncio (Testing)

The entire application is async. Standard pytest cannot test async functions without `pytest-asyncio`. We used `aiosqlite` as an in-memory test database so tests run without requiring a real PostgreSQL instance — making tests fast, portable, and CI-friendly.

**Cost: Free and open source.**

---

## 7. Sprint 1 — Core Consumer & Email Notification

### Sprint Goal
Stand up the core infrastructure: RabbitMQ consumer, event validation pipeline, email notification for payslips, and the notification history API.

### Stories Delivered
- US-002 — Payslip Email with Attachment ✅
- US-006 — Notification History API ✅
- Core infrastructure for all subsequent sprints ✅

---

### What We Built

#### RabbitMQ Consumer (`app/consumers/payroll_consumer.py`)

The consumer is the entry point of the entire system. On startup, it connects to RabbitMQ and declares all required infrastructure:

- **Main Exchange** — `payroll_events` (topic type) — the payroll system publishes events here
- **Main Queue** — `notification_queue` (durable) — our consumer reads from here
- **Routing Pattern** — `payroll.#` — matches any routing key starting with `payroll.`
- **Dead Letter Exchange** — `payroll_events.dlx` — receives messages after retry exhaustion
- **Dead Letter Queue** — `notification_dlq` — stores messages for manual inspection and reprocessing

**Why topic exchange?** Topic exchanges enable flexible routing by pattern. `payroll.salary`, `payroll.bonus`, and `payroll.payslip` all match `payroll.#`. Adding a new event type requires no exchange configuration change — just a new routing key and handler.

**Why durable queues?** Durable queues survive RabbitMQ restarts. Without durability, any pending notifications would vanish if the broker restarts — completely unacceptable in a financial notification system.

```python
# Consumer declares queue with automatic DLQ routing
queue = await channel.declare_queue(
    "notification_queue",
    durable=True,
    arguments={"x-dead-letter-exchange": "payroll_events.dlx"}
)
await queue.bind(exchange, routing_key="payroll.#")
```

#### Event Validation (`app/schemas/events.py`)

Every incoming event is validated against a strict Pydantic schema before any processing begins. This means:

- All required fields must be present
- Data types must match (string, integer, ISO datetime)
- Malformed or incomplete events are rejected with detailed error logs
- The Developer never needs to write manual field-checking code

Each event type has its own payload schema nested inside a common base:

```
BaseEvent               → event_id, event_type, timestamp, auth_token, employee contact
  └─ SalaryCreditedPayload    → month, year, net_salary, currency, transaction_reference
  └─ PayslipGeneratedPayload  → month, year, gross_salary, deductions, net_salary, payslip_pdf_url
  └─ BonusCreditedPayload     → bonus_type, amount, currency, transaction_reference
  └─ OvertimeCalculatedPayload → month, year, total_overtime_hours, overtime_amount, overtime_pdf_url
  └─ BankDetailsUpdatedPayload → masked_account_number, updated_at
```

**Why validate at the entry point?** An invalid event that slips through to the channel services causes unclear errors deep in the stack. Pydantic validation at the consumer boundary produces clean, loggable errors at the point of entry and prevents any downstream processing of bad data.

#### Email Service (`app/channels/email_service.py`)

The email service handles two scenarios gracefully:

**Scenario 1 — Email with PDF attachment (primary path)**
1. Downloads PDF from the URL provided in the event payload using `httpx` (async HTTP client)
2. Attaches the downloaded PDF to a MIME email
3. Sends via `aiosmtplib` (async SMTP client)
4. Records the delivery in the database

**Scenario 2 — Email without attachment (graceful degradation)**
- If PDF download fails (invalid URL, server down, network issue), a warning is logged
- The email is still sent without the attachment rather than failing entirely
- This is a deliberate resilience decision: an employee receiving the notification body is better than receiving nothing, and the failure is recorded for follow-up

**Why aiosmtplib over standard smtplib?** Standard `smtplib` is synchronous. A synchronous SMTP call in our async application would block the entire event loop while waiting for the SMTP handshake — preventing any other events from being processed in parallel. `aiosmtplib` is the async equivalent and integrates naturally with our architecture.

**Mock mode:** When no SMTP credentials are configured, the service logs the email content to the console instead of attempting a real send. This enables development and local testing without credentials.

#### Notification History API (`app/api/routes.py`)

Two endpoints delivered in Sprint 1:

```
GET /health                      → Returns service status (UP)
GET /notifications/{employee_id} → Returns full notification history for an employee
```

The history endpoint queries the `notifications` table filtered by employee ID and returns a structured JSON list. Payroll administrators can verify delivery status, confirm what was sent, and resolve employee disputes about missing notifications.

**Interactive Swagger UI is automatically available at:** `http://localhost:8000/docs`

#### Database Schema and Migrations (`app/models/notification.py`, `migrations/`)

Two tables created via Alembic migration:

```sql
notifications (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id  VARCHAR NOT NULL,
    event_type   VARCHAR NOT NULL,
    channel_type VARCHAR NOT NULL,  -- SMS or EMAIL
    status       VARCHAR NOT NULL,  -- PENDING, SENT, FAILED
    retry_count  INTEGER DEFAULT 0,
    created_at   TIMESTAMP DEFAULT now(),
    updated_at   TIMESTAMP DEFAULT now()
)

notification_logs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id  UUID REFERENCES notifications(id) ON DELETE CASCADE,
    response_message TEXT,   -- provider success response
    error_message    TEXT,   -- error details on failure
    timestamp        TIMESTAMP DEFAULT now()
)
```

Every notification creates a `notifications` record. Every delivery attempt (including retries) creates a `notification_logs` record. This gives complete audit visibility — you can see not just the final outcome but the full attempt history.

---

### Sprint 1 Review

| Story | Status | Notes |
|-------|--------|-------|
| US-002 Payslip Email | ✅ Done | Real email with PDF attachment working |
| US-006 History API | ✅ Done | `GET /notifications/{id}` returning correct structured data |
| Core infrastructure | ✅ Done | Consumer, DB, validation, logging all operational |

---

## 8. Sprint 2 — SMS, Attachments & All Five Events

### Sprint Goal
Complete all five event types end-to-end. Integrate real SMS via Twilio. Ensure every event type produces the correct notification through the correct channel.

### Stories Delivered
- US-001 — Salary Credit SMS ✅
- US-003 — Bonus Credit SMS ✅
- US-004 — Overtime Statement Email ✅
- US-005 — Bank Details Security Alert SMS ✅

---

### What We Built

#### SMS Service (`app/channels/sms_service.py`)

The SMS service integrates with **Twilio** as the real delivery provider.

**How it works:**
1. Receives the employee phone number and rendered message text from the notification service
2. Calls Twilio's REST API using the official `twilio` Python SDK
3. Twilio delivers the SMS to the employee's phone within seconds
4. Returns the Twilio message SID as a unique delivery confirmation
5. Logs the SID and delivery status in the database

**Why Twilio?** Twilio is the industry standard for programmable SMS. It provides a free trial with real delivery, a simple SDK, reliable delivery to Indian numbers (`+91`), and delivery confirmation through message SIDs — which we store in our audit log.

**Phone number formatting:** The service automatically prepends `+91` (India country code) to the phone number from the event payload. This would be made configurable for multi-country deployment.

#### Template Processor (`app/templates/`)

Each event type produces a different notification message. The template processor uses Jinja2 to render messages dynamically by injecting event data into predefined templates.

**SMS Templates:**

`SalaryCredited`:
```
Your salary for {{ month }} {{ year }} has been credited successfully.
Amount: ₹{{ net_salary }}
Ref: {{ transaction_reference }}
```

`BonusCredited`:
```
Congratulations {{ name }}! Your {{ bonus_type }} of ₹{{ amount }} has been credited.
Ref: {{ transaction_reference }}
```

`BankDetailsUpdated`:
```
Dear {{ name }}, your bank account ({{ masked_account_number }}) has been updated
successfully. If this wasn't you, contact HR immediately.
```

**Email Templates:**

`PayslipGenerated`:
```
Subject: Payslip for {{ month }} {{ year }}

Dear {{ name }},
Your payslip for {{ month }} {{ year }} is attached.
Net Salary: ₹{{ net_salary }}
```

`OvertimeCalculated`:
```
Subject: Overtime Statement for {{ month }} {{ year }}

Dear {{ name }},
Your overtime statement for {{ month }} {{ year }} is ready.
Total Hours: {{ total_overtime_hours }}
Overtime Amount: ₹{{ overtime_amount }}
```

**Why Jinja2 templates?** Templates separate content from code. Adding a new event type requires only a new template file — no changes to the service logic. Templates are readable by non-developers, making content easier to review, update, and localize.

#### Channel Routing Logic (`app/services/notification_service.py`)

The notification service automatically routes each event type to the correct channel based on a routing configuration:

```
SalaryCredited     → SMS
PayslipGenerated   → Email (with PDF attachment)
BonusCredited      → SMS
OvertimeCalculated → Email (with PDF attachment)
BankDetailsUpdated → SMS
```

This routing is defined in the template configuration, not hardcoded in conditional logic. Adding a new event with a new channel requires only a new template entry — the routing engine handles the rest.

#### Contact Validation

Before dispatching, the service validates that the required contact information is present:

- SMS events require `employee.phone` — missing phone rejects the event with a clear error
- Email events require `employee.email` — missing email rejects the event with a clear error

This prevents silent failures where a notification appears to succeed but the message was never sent because contact information was absent.

---

### Sprint 2 Review

| Story | Status | Notes |
|-------|--------|-------|
| US-001 Salary SMS | ✅ Done | Real SMS delivered via Twilio — confirmed with 201 response and message SID |
| US-003 Bonus SMS | ✅ Done | Working end to end |
| US-004 Overtime Email | ✅ Done | Email with PDF attachment delivered |
| US-005 Bank Alert SMS | ✅ Done | Security alert SMS working |

---

## 9. Sprint 3 — Retry, Dead Letter Queue & Security

### Sprint Goal
Make the system production-reliable. Automatic retry on transient failures, dead letter handling for permanent failures, and security token validation to restrict event access.

### Stories Delivered
- US-007 — Retry on Failure with Dead Letter Queue ✅
- US-008 — Security Token Validation ✅

---

### What We Built

#### Retry Mechanism with Exponential Backoff (`app/services/retry_service.py`)

The retry service implements **exponential backoff** — the industry-standard reliability pattern used by AWS, Google, and all major cloud providers.

**How it works:**

```
Attempt 0 (immediate):  → Notification service tries to send
  └─ Fails              → Wait 1 second
Attempt 1 (retry 1):    → Try again
  └─ Fails              → Wait 2 seconds
Attempt 2 (retry 2):    → Try again
  └─ Fails              → Wait 4 seconds
Attempt 3 (retry 3):    → Try again
  └─ Fails              → Publish to Dead Letter Queue
```

**Why exponential backoff over linear retry?** Linear retry (try every 1 second) hammers a struggling service and can worsen an overload situation. Exponential backoff gives the failing gateway increasingly more time to recover between attempts. This is the industry standard precisely because it is more respectful of downstream services under stress.

**Why 3 retries?** Three retries balance reliability against resource consumption. More retries would delay processing of other events in the queue; fewer retries might miss recoverable transient failures. Three attempts covers the vast majority of transient network or gateway issues.

**Why Dead Letter Queue instead of discarding?** In a financial notification system, discarding a failed message is unacceptable. The employee may never know their salary was credited. The DLQ captures all permanently failed messages so they can be inspected, the underlying cause resolved, and the messages reprocessed manually — zero message loss.

```python
async def retry_with_backoff(func, event_data, dlq_publisher,
                              max_retries=3, base_delay=1):
    attempt = 0
    while attempt <= max_retries:
        try:
            await func(event_data)
            return  # success
        except Exception as e:
            if attempt == max_retries:
                await dlq_publisher(event_data)
                return
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            await asyncio.sleep(delay)
            attempt += 1
```

Every retry attempt is logged with attempt number, delay duration, and the exact error — providing complete visibility into failure patterns for operational analysis.

#### Security Token Validation (`app/security/validator.py`)

Every incoming event must carry a valid `auth_token`. Validation is the first step before any processing begins.

**How it works:**
- Valid tokens are defined in service configuration via environment variable
- Each event's `auth_token` field is checked against the authorized token set
- Invalid token → event immediately rejected → rejection logged → no notification sent

**Why auth token validation?** Without this, any service that can publish to RabbitMQ can trigger employee notifications. RabbitMQ username and password provide network-level security. The auth token provides **application-level security** — ensuring only the authorized payroll system can trigger notifications, even if other internal services have queue access.

**Sensitive Data Masking in Logs:**

All logs mask personal contact information to prevent accidental exposure:

| Data | Raw | Logged As |
|------|-----|-----------|
| Phone | `9876543210` | `******3210` |
| Email | `arun@company.com` | `ar**@company.com` |
| Account | Already masked by payroll | `XXXX1234` |

This ensures logs can be shared with support teams or stored long-term without exposing personal data — critical for compliance in a financial system.

---

### Sprint 3 Review

| Story | Status | Notes |
|-------|--------|-------|
| US-007 Retry + DLQ | ✅ Done | 3 retries, exponential backoff confirmed, DLQ routing working |
| US-008 Security | ✅ Done | Token validation, data masking in all logs |

---

## 10. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PAYROLL SYSTEM                                │
│              (Salary Engine — Outside Our Scope)                     │
│   Calculates salary → Processes bank transfer → Generates PDFs       │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ Publishes structured JSON events
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        RABBITMQ BROKER                               │
│   Exchange:  payroll_events (topic)                                  │
│   Queue:     notification_queue (durable, DLQ-backed)                │
│   DLQ:       notification_dlq (failed messages for inspection)       │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ Async event consumption
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  NOTIFICATION MICROSERVICE (FastAPI)                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PayrollEventConsumer  (aio-pika async consumer)             │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
│                               │                                      │
│  ┌────────────────────────────▼─────────────────────────────────┐   │
│  │  Security Validator  (auth_token check → reject if invalid)  │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
│                               │                                      │
│  ┌────────────────────────────▼─────────────────────────────────┐   │
│  │  Pydantic Schema Validator  (strict event contract check)    │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
│                               │                                      │
│  ┌────────────────────────────▼─────────────────────────────────┐   │
│  │  Jinja2 Template Renderer  (dynamic message generation)      │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
│                               │                                      │
│                  ┌────────────┴────────────┐                         │
│                  │                         │                         │
│  ┌───────────────▼──────────┐  ┌───────────▼──────────┐            │
│  │     Email Service        │  │      SMS Service      │            │
│  │  (aiosmtplib + PDF att.) │  │  (Twilio SDK)         │            │
│  └───────────────┬──────────┘  └───────────┬──────────┘            │
│                  │                         │                         │
│  ┌───────────────▼─────────────────────────▼──────────────────┐    │
│  │              PostgreSQL Audit Database                       │    │
│  │   notifications table  +  notification_logs table            │    │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Retry Service  (exponential backoff → DLQ after 3 retries)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  REST API:  GET /health   │   GET /notifications/{id}        │   │
│  │  Swagger UI automatically at  http://localhost:8000/docs      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                  │                         │
                  ▼                         ▼
         📧 Employee Email           📱 Employee Phone
        (Gmail SMTP — real)        (Twilio SMS — real)
```
![System Architecture](images/archi.jpeg)
---

## 11. Project Structure

```
notification_service/
│
├── app/
│   ├── main.py                       # FastAPI app entry point, startup/shutdown hooks
│   │
│   ├── config/
│   │   ├── settings.py               # Pydantic-based environment config (all from .env)
│   │   └── logging.py                # structlog structured JSON logging configuration
│   │
│   ├── consumers/
│   │   └── payroll_consumer.py       # aio-pika async RabbitMQ consumer
│   │
│   ├── services/
│   │   ├── notification_service.py   # Core orchestration: validates → renders → dispatches
│   │   └── retry_service.py          # Exponential backoff retry + DLQ routing
│   │
│   ├── channels/
│   │   ├── email_service.py          # Async SMTP with PDF attachment download
│   │   └── sms_service.py            # Twilio SMS integration with async executor
│   │
│   ├── templates/
│   │   ├── message_templates.py      # Jinja2 template strings for all 5 event types
│   │   └── renderer.py               # Template rendering engine
│   │
│   ├── models/
│   │   └── notification.py           # SQLAlchemy ORM: notifications + notification_logs
│   │
│   ├── schemas/
│   │   └── events.py                 # Pydantic validation schemas for all 5 events
│   │
│   ├── db/
│   │   └── base.py                   # Async PostgreSQL engine + session factory
│   │
│   ├── security/
│   │   └── validator.py              # Auth token validation + sensitive data masking
│   │
│   └── api/
│       └── routes.py                 # REST endpoints: /health + /notifications/{id}
│
├── migrations/
│   ├── env.py                        # Alembic async migration environment
│   └── versions/
│       └── 0001_initial.py           # Initial schema: notifications + logs tables
│
├── tests/
│   ├── conftest.py                   # In-memory SQLite test DB setup (no PostgreSQL needed)
│   ├── test_event_validation.py      # Pydantic schema tests — valid and invalid events
│   ├── test_notification_service.py  # Orchestration tests with mocked channels
│   └── test_retry.py                 # Retry logic and DLQ routing tests
│
├── .env                              # Environment variables (never commit to git)
├── alembic.ini                       # Alembic migration configuration
├── pytest.ini                        # Test configuration
├── requirements.txt                  # All Python dependencies pinned to exact versions
└── README.md                         # This document
```

---

## 12. Event Input Contracts

All events published to RabbitMQ must follow this structure. The service validates every field before processing begins. Invalid events are rejected and logged.

### Common Base Structure

```json
{
  "event_id": "unique string identifier per event",
  "event_type": "one of the five supported event types",
  "timestamp": "ISO-8601 datetime e.g. 2026-02-28T10:15:00Z",
  "auth_token": "must match the configured AUTH_TOKEN",
  "employee": {
    "employee_id": "EMP001",
    "name": "Full Name",
    "email": "required for email events",
    "phone": "required for SMS events"
  },
  "payload": { }
}
```

---

### Event 1 — SalaryCredited

**Routing Key:** `payroll.salary` | **Channel:** SMS

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
  "payload": {
    "month": "February",
    "year": 2026,
    "net_salary": 45000,
    "currency": "INR",
    "transaction_reference": "TXN9845123"
  }
}
```

**SMS Delivered:**
```
Your salary for February 2026 has been credited successfully.
Amount: ₹45,000 | Ref: TXN9845123
```

---

### Event 2 — PayslipGenerated

**Routing Key:** `payroll.payslip` | **Channel:** Email + PDF Attachment

```json
{
  "event_id": "evt-1002",
  "event_type": "PayslipGenerated",
  "timestamp": "2026-02-28T09:00:00Z",
  "auth_token": "secure-token",
  "employee": {
    "employee_id": "EMP002",
    "name": "Priya Sharma",
    "email": "priya@example.com"
  },
  "payload": {
    "month": "February",
    "year": 2026,
    "gross_salary": 52000,
    "deductions": 7000,
    "net_salary": 45000,
    "payslip_pdf_url": "https://www.africau.edu/images/default/sample.pdf"
  }
}
```

**Email Delivered:**
```
Subject: Payslip for February 2026
Body: Dear Priya Sharma, Your payslip for February 2026 is attached. Net Salary: ₹45,000
Attachment: payslip PDF downloaded from the provided URL
```

---

### Event 3 — BonusCredited

**Routing Key:** `payroll.bonus` | **Channel:** SMS

```json
{
  "event_id": "evt-1003",
  "event_type": "BonusCredited",
  "timestamp": "2026-03-05T12:00:00Z",
  "auth_token": "secure-token",
  "employee": {
    "employee_id": "EMP003",
    "name": "Ravi Shankar",
    "phone": "9876543210"
  },
  "payload": {
    "bonus_type": "Performance Bonus",
    "amount": 10000,
    "currency": "INR",
    "transaction_reference": "TXN1112233"
  }
}
```

**SMS Delivered:**
```
Congratulations Ravi Shankar! Your Performance Bonus of ₹10,000 has been credited.
Ref: TXN1112233
```

---

### Event 4 — OvertimeCalculated

**Routing Key:** `payroll.overtime` | **Channel:** Email + PDF Attachment

```json
{
  "event_id": "evt-1004",
  "event_type": "OvertimeCalculated",
  "timestamp": "2026-02-27T16:00:00Z",
  "auth_token": "secure-token",
  "employee": {
    "employee_id": "EMP004",
    "name": "Meena Devi",
    "email": "meena@example.com"
  },
  "payload": {
    "month": "February",
    "year": 2026,
    "total_overtime_hours": 18,
    "overtime_amount": 3500,
    "overtime_pdf_url": "https://www.africau.edu/images/default/sample.pdf"
  }
}
```

**Email Delivered:**
```
Subject: Overtime Statement for February 2026
Body: Dear Meena Devi, Your overtime statement is ready.
      Total Hours: 18 | Overtime Amount: ₹3,500
Attachment: overtime PDF
```

---

### Event 5 — BankDetailsUpdated

**Routing Key:** `payroll.bank` | **Channel:** SMS (Security Alert)

```json
{
  "event_id": "evt-1005",
  "event_type": "BankDetailsUpdated",
  "timestamp": "2026-02-20T14:00:00Z",
  "auth_token": "secure-token",
  "employee": {
    "employee_id": "EMP005",
    "name": "Karthik Raja",
    "phone": "9876543210"
  },
  "payload": {
    "masked_account_number": "XXXX1234",
    "updated_at": "2026-02-20T13:59:00Z"
  }
}
```

**SMS Delivered:**
```
Dear Karthik Raja, your bank account (XXXX1234) has been updated successfully.
If this wasn't you, contact HR immediately.
```
![System Architecture](images/rabbitmq.png)
---

## 13. Database Design

### Table: notifications

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Auto-generated primary key |
| employee_id | VARCHAR | Employee identifier from the event |
| event_type | VARCHAR | SalaryCredited, PayslipGenerated, etc. |
| channel_type | VARCHAR | SMS or EMAIL |
| status | VARCHAR | PENDING → SENT or FAILED |
| retry_count | INTEGER | Number of retry attempts made (0–3) |
| created_at | TIMESTAMP | When the notification was first created |
| updated_at | TIMESTAMP | When the record was last updated |

![System Architecture](images/db1.png)

### Table: notification_logs

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Auto-generated primary key |
| notification_id | UUID FK | Links to the parent notifications record |
| response_message | TEXT | Success response from the provider (e.g., Twilio SID) |
| error_message | TEXT | Error details on failure |
| timestamp | TIMESTAMP | When this log entry was created |

![System Architecture](images/db2.png)


**Why two tables?** The `notifications` table tracks the overall delivery outcome. The `notification_logs` table tracks every individual attempt — including all retries. This separation gives complete audit visibility without bloating the main notifications record with retry details.


---

## 14. REST API Reference

### GET /health

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "UP",
  "service": "notification-service"
}
```
![System Architecture](images/health.png)

---

### GET /notifications/{employee_id}

```bash
curl http://localhost:8000/notifications/EMP001
```

```json
[
  {
    "notification_id": "b858e3e6-05e0-41e0-924d-4c83ab960e02",
    "event_type": "SalaryCredited",
    "channel": "SMS",
    "status": "SENT",
    "retry_count": 0,
    "timestamp": "2026-02-28T10:15:00Z"
  },
  {
    "notification_id": "c6f43007-42be-4572-8e14-a4bb30c46db9",
    "event_type": "PayslipGenerated",
    "channel": "EMAIL",
    "status": "SENT",
    "retry_count": 0,
    "timestamp": "2026-02-28T09:00:00Z"
  }
]
```

**Swagger UI (interactive, auto-generated):** `http://localhost:8000/docs`
![System Architecture](images/empstatus.png)

---

## 15. Testing

### Testing Philosophy

We followed a layered testing approach — testing each component in isolation before testing interactions between components. All tests use an in-memory SQLite database so the test suite runs without any external dependencies.

---

### Test Layer 1 — Event Validation Tests (`test_event_validation.py`)

Verifies that Pydantic schemas correctly enforce the event contract at the system boundary.

**What we tested:**
- Valid events with all required fields pass without errors
- Events with empty `auth_token` are rejected with `ValidationError`
- Events missing `event_type` or `event_id` are rejected
- Each payload schema validates correctly for its specific event type
- Missing required payload fields (e.g., `payslip_pdf_url`) raise `ValidationError`
- Extra unexpected fields in the payload are handled gracefully

**Why this matters:** If validation is wrong, malformed data reaches the channel services and causes unclear errors deep in the stack. These tests guarantee the contract is enforced cleanly at the system boundary.

```python
def test_missing_auth_token_raises():
    data = {**VALID_BASE, "auth_token": ""}
    with pytest.raises(ValidationError):
        BaseEvent(**data)

def test_payslip_payload_missing_url_raises():
    data = {**VALID_PAYSLIP_EVENT}
    del data["payload"]["payslip_pdf_url"]
    with pytest.raises(ValidationError):
        PayslipGeneratedEvent(**data)
```

**Result: 6 tests — all passing ✅**

---

### Test Layer 2 — Notification Service Tests (`test_notification_service.py`)

Verifies the core orchestration logic — that the correct channel is called for each event type, the database record is created accurately, and security validation blocks unauthorized events.

**What we tested:**
- `SalaryCredited` event triggers `SMSService.send()` with the correct phone number and rendered message
- `PayslipGenerated` event triggers `EmailService.send()` with correct email, subject, and PDF URL
- Event with invalid auth token raises `PermissionError` and no channel is called
- Unknown event type raises `ValueError` and no channel is called
- Successfully processed notifications are recorded in database with status `SENT`
- Failed notifications are recorded with status `FAILED`

**How we tested without real SMS/Email:** We used `pytest-mock` to replace `SMSService.send` and `EmailService.send` with `AsyncMock` functions. This verifies the correct service was called with the correct arguments without triggering real delivery — making tests fast, deterministic, and idempotent.

```python
async def test_salary_credited_routes_to_sms(db_session):
    with patch("app.services.notification_service.SMSService.send",
               new_callable=AsyncMock) as mock_sms:
        mock_sms.return_value = {"status": "SENT", "message_id": "SM123"}
        service = NotificationService(db_session)
        await service.process_event(SALARY_EVENT)
        mock_sms.assert_called_once()
        args = mock_sms.call_args[0]
        assert args[0] == "9876543210"  # correct phone

async def test_invalid_auth_raises_permission_error(db_session):
    invalid_event = {**SALARY_EVENT, "auth_token": "wrong-token"}
    service = NotificationService(db_session)
    with pytest.raises(PermissionError):
        await service.process_event(invalid_event)
```

**Result: 5 tests — all passing ✅**

---

### Test Layer 3 — Retry Logic Tests (`test_retry.py`)

Verifies the retry mechanism behaves exactly as specified in US-007.

**What we tested:**
- A successful first attempt does not trigger any retry (function called exactly once)
- A function that fails twice then succeeds on the third attempt completes successfully with total 3 calls
- After max retries are exhausted, the Dead Letter Queue publisher is called exactly once
- Setting `max_retries=0` results in exactly one attempt followed by immediate DLQ routing
- Retry delays follow the exponential backoff formula (1s, 2s, 4s)

**Why these tests are critical:** Retry logic is complex and easy to get subtly wrong. An off-by-one error (4 retries instead of 3) or a DLQ publisher that is never called are silent bugs that only appear in production when an employee misses a salary notification. Unit tests catch these before deployment.

```python
async def test_exhausted_retries_sends_to_dlq():
    func = AsyncMock(side_effect=Exception("permanent failure"))
    dlq = AsyncMock()
    await retry_with_backoff(func, DUMMY_EVENT, dlq,
                              max_retries=3, base_delay=0)
    assert func.call_count == 4  # initial + 3 retries
    dlq.assert_called_once_with(DUMMY_EVENT)

async def test_succeeds_on_third_attempt_no_dlq():
    call_count = 0
    async def flaky_func(event):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("transient failure")
    dlq = AsyncMock()
    await retry_with_backoff(flaky_func, DUMMY_EVENT, dlq,
                              max_retries=3, base_delay=0)
    assert call_count == 3
    dlq.assert_not_called()  # DLQ must NOT be called on eventual success
```

**Result: 4 tests — all passing ✅**

---

### Running the Test Suite

```bash
cd notification_service
venv\Scripts\activate
pytest -v
```

Expected output:
```
tests/test_event_validation.py::test_valid_base_event_passes              PASSED
tests/test_event_validation.py::test_missing_auth_token_raises            PASSED
tests/test_event_validation.py::test_missing_event_type_raises            PASSED
tests/test_event_validation.py::test_salary_payload_valid                 PASSED
tests/test_event_validation.py::test_payslip_payload_missing_url_raises   PASSED
tests/test_event_validation.py::test_bank_details_payload_valid           PASSED
tests/test_notification_service.py::test_salary_credited_routes_to_sms   PASSED
tests/test_notification_service.py::test_payslip_routes_to_email          PASSED
tests/test_notification_service.py::test_invalid_auth_raises_permission   PASSED
tests/test_notification_service.py::test_unknown_event_raises_value_err  PASSED
tests/test_notification_service.py::test_sent_notification_saved_to_db   PASSED
tests/test_retry.py::test_succeeds_first_try_no_retry                     PASSED
tests/test_retry.py::test_succeeds_on_third_attempt_no_dlq               PASSED
tests/test_retry.py::test_exhausted_retries_sends_to_dlq                  PASSED
tests/test_retry.py::test_zero_max_retries_immediate_dlq                  PASSED

15 passed in 2.41s
```
![System Architecture](images/testing.png)

---

## 16. Setup & Running the Project

### Prerequisites

- Python 3.9 or higher
- PostgreSQL running locally (create a database named `notifications`)
- RabbitMQ running locally (management plugin enabled)
- Twilio account (free trial is sufficient)
- Gmail account with 2FA and an App Password

### Step 1 — Create Virtual Environment and Install Dependencies

```bash
cd notification_service
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### Step 2 — Create `.env` File

Create a file named `.env` in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notifications
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
AUTH_TOKEN=secure-token

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM_EMAIL=your@gmail.com
SMTP_FROM_NAME=Payroll System

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1xxxxxxxxxx

DEBUG=True
```

**Getting Gmail App Password:**
1. Go to `https://myaccount.google.com/security`
2. Enable 2-Step Verification
3. Go to `https://myaccount.google.com/apppasswords`
4. Create an App Password named "Payroll" — copy the 16-character password (remove spaces)

**Getting Twilio Credentials:**
1. Sign up free at `https://console.twilio.com`
2. Copy Account SID, Auth Token, and the trial phone number from the dashboard
3. Verify your personal phone number to receive SMS on the free trial

### Step 3 — Run Database Migrations

```bash
alembic upgrade head
```

### Step 4 — Start the Service

```bash
uvicorn app.main:app --port 8000 --reload
```

Service is ready when you see:
```
"event": "rabbitmq_consumer_started"
"event": "service_started"
INFO: Application startup complete.
```

### Step 5 — Verify

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- RabbitMQ dashboard: `http://localhost:15672` (guest/guest)

---

## 17. Live Demo — Testing All Five Events

Open RabbitMQ at `http://localhost:15672` → **Exchanges** → `payroll_events` → **Publish message**

Use the routing key and payload for each event. After publishing, check:
- Terminal logs for structured JSON output
- `http://localhost:8000/notifications/{employee_id}` for the database record
- Your phone or email for the actual delivered notification

| # | Event | Routing Key | Channel | What You Receive |
|---|-------|------------|---------|-----------------|
| 1 | SalaryCredited | `payroll.salary` | 📱 SMS | Salary credit alert on phone |
| 2 | PayslipGenerated | `payroll.payslip` | 📧 Email | Payslip email with PDF attached |
| 3 | BonusCredited | `payroll.bonus` | 📱 SMS | Bonus credit alert on phone |
| 4 | OvertimeCalculated | `payroll.overtime` | 📧 Email | Overtime statement email with PDF |
| 5 | BankDetailsUpdated | `payroll.bank` | 📱 SMS | Security alert SMS |

![System Architecture](images/event1.jpeg)
![System Architecture](images/event2.jpeg)
![System Architecture](images/event3.jpeg)
![System Architecture](images/event4.jpeg)
![System Architecture](images/event5.jpeg)



**Payloads for each event are in [Section 12](#12-event-input-contracts).**

**Testing Retry and DLQ (Optional Demo):**
Temporarily set an invalid `TWILIO_AUTH_TOKEN` in `.env`, publish a `SalaryCredited` event, and watch in the terminal:
```
"event": "notification_failed", "attempt": 1 → "delay_seconds": 1
"event": "notification_failed", "attempt": 2 → "delay_seconds": 2
"event": "notification_failed", "attempt": 3 → "delay_seconds": 4
"event": "message_sent_to_dlq"
```
Then check `notification_dlq` in RabbitMQ dashboard — your message is safely queued for reprocessing.

---

## 18. What We Have Not Implemented — Future Scope

We were deliberate about scope. The following were identified during Sprint Zero but not implemented in this delivery. Each item has a clear upgrade path.

---

### 🔲 In-App Notification Channel

**What it is:** Push notifications inside a web or mobile application — a notification bell icon that shows unread alerts when the employee logs in.

**Why not implemented:** Requires a frontend application, WebSocket server, and device token management — a significant scope increase beyond the notification microservice boundary.

**Upgrade path:** Add a WebSocket endpoint in FastAPI. Store device tokens per employee in the database. Add an `InAppService` class in `app/channels/`. Add `IN_APP` as a routable channel type in the template configuration. The existing consumer and orchestration code needs no changes — only a new channel implementation.

---

### 🔲 Notification Dashboard UI

**What it is:** A web interface for payroll administrators showing delivery statistics — total sent, total failed, retry rates, per-employee history, charts by event type and channel.

**Why not implemented:** Frontend development is outside the microservice scope and would require a separate project.

**Upgrade path:** Build a React or Vue SPA that queries existing REST endpoints. Add aggregate analytics endpoints (`GET /notifications/stats`, `GET /notifications/stats/by-event-type`) to the FastAPI service. The underlying data is already fully captured in the database — the dashboard is purely a visualization layer.

---

### 🔲 WhatsApp Notification Channel

**What it is:** Salary and bonus alerts delivered via WhatsApp Business API — more effective than SMS for employees who primarily communicate over WhatsApp.

**Why not implemented:** Requires WhatsApp Business API approval, a registered business phone number, and message template approval — significant lead time.

**Upgrade path:** Twilio supports WhatsApp through the exact same SDK used for SMS (`client.messages.create(to="whatsapp:+91...")`). Add a `WhatsAppService` in `app/channels/`. Route specific events to WhatsApp based on employee preference settings.

---

### 🔲 Employee Notification Preferences

**What it is:** Allowing employees to select their preferred channel — "I want salary alerts on SMS but payslips only on email."

**Why not implemented:** Requires an employee preferences database table and a preference management API — additional scope beyond notification delivery.

**Upgrade path:** Add a `notification_preferences` table (`employee_id`, `event_type`, `preferred_channel`). Before routing, query the employee's preference. Override the default channel routing in `notification_service.py` based on the queried preference.

---

### 🔲 JWT Token Authentication

**What it is:** Replacing the static shared auth token with JWT (JSON Web Token) — a signed, expiring, tamper-proof industry-standard authentication mechanism.

**Why not implemented:** The static token is sufficient for demonstration purposes. JWT adds implementation complexity without changing the demo outcome.

**Upgrade path:** Use `python-jose` (already listed in requirements). The payroll system issues signed JWT tokens with an expiry. The notification service verifies the token signature using a shared public key. Tokens that are expired, tampered with, or from unauthorized issuers are rejected. This upgrade requires only changes to `app/security/validator.py`.

---

### 🔲 Notification Rate Limiting and Deduplication

**What it is:** Preventing duplicate notifications if payroll accidentally publishes the same event multiple times. For example, if the same `SalaryCredited` event with `event_id: evt-1001` is published twice, the employee should receive only one SMS.

**Upgrade path:** Add a Redis cache. Before sending, check if a notification for the same `event_id` has already been processed. If yes, skip and log as duplicate. `event_id` in the current schema is already designed for this — it exists specifically to enable deduplication.

---

### 🔲 HTML Email Templates

**What it is:** Rich HTML emails with company branding, logo, color scheme, and formatted salary tables — instead of the current plain-text emails.

**Upgrade path:** Create HTML Jinja2 templates alongside the current text templates. Use `email.mime.multipart.MIMEMultipart("alternative")` to send both plain-text and HTML versions in the same email. Email clients display whichever version they support. This upgrade requires only new template files and a minor update to `email_service.py`.

---

### 🔲 SMS Delivery Confirmation Webhooks

**What it is:** Twilio can call back our service when an SMS is actually delivered to the handset (not just accepted by the gateway). This allows updating notification status from `SENT` to `DELIVERED` with real confirmation.

**Upgrade path:** Add `POST /webhooks/twilio/status` endpoint to FastAPI. Pass the webhook URL to Twilio when creating messages (`status_callback=url`). On receipt, look up the notification by Twilio message SID (stored in `notification_logs.response_message`) and update status.

---

### 🔲 Multi-Environment Configuration

**What it is:** Separate configuration profiles for development, staging, and production — different RabbitMQ instances, different credentials, different log levels, different Twilio accounts.

**Upgrade path:** Use environment-specific `.env` files (`.env.dev`, `.env.staging`, `.env.prod`). Set `ENV=dev` as an environment variable. Load the correct file in `settings.py` using Pydantic's `model_config`. All settings code stays the same — only the loaded file changes per environment.

---

## 📌 Summary

This project demonstrates a complete, production-grade event-driven microservice built with proper Agile Scrum methodology. From Sprint Zero discovery through three focused delivery sprints, every decision was made deliberately with a traceable business reason.

### What This System Does

| Capability | Status |
|-----------|--------|
| Consumes real payroll events from RabbitMQ | ✅ Working |
| Validates every event against strict Pydantic schemas | ✅ Working |
| Validates security auth token on every event | ✅ Working |
| Routes events to the correct channel (SMS or Email) | ✅ Working |
| Renders dynamic messages with Jinja2 templates | ✅ Working |
| Sends real SMS via Twilio | ✅ Working — confirmed with 201 HTTP response |
| Sends real email via Gmail SMTP | ✅ Working |
| Downloads and attaches PDF from URL to email | ✅ Working |
| Degrades gracefully if PDF download fails | ✅ Working |
| Retries failed deliveries with exponential backoff | ✅ Working |
| Routes permanently failed messages to DLQ | ✅ Working |
| Logs every action in structured JSON format | ✅ Working |
| Masks sensitive data (phone, email) in all logs | ✅ Working |
| Creates immutable audit record per notification | ✅ Working |
| Provides REST API for notification history | ✅ Working |
| Auto-generates interactive Swagger documentation | ✅ Working |
| 15 unit tests covering all critical paths | ✅ Passing |

### Our Scrum Delivery

```
Sprint Zero  →  Domain analysis, user stories, architecture decision, event contracts
Sprint 1     →  RabbitMQ consumer, Pydantic validation, Email service, History API
Sprint 2     →  Twilio SMS, all 5 event types, channel routing, Jinja2 templates
Sprint 3     →  Exponential backoff retry, Dead Letter Queue, Security token validation
```

**Total Story Points Delivered: 25 / 25**

> *Every technology decision is explained. Every trade-off is documented.*
> *Every line of this README maps to a business reason, a user story, or a sprint activity.*
> *This is not just a working system — it is a traceable Agile delivery.*

---

*Problem statement: "Build a Notification System for a Payroll System"*
*Our answer: A production-grade event-driven microservice — designed, decided, and delivered the Agile way.*

