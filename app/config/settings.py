from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "notification-service"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notifications"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "payroll_events"
    RABBITMQ_QUEUE: str = "notification_queue"
    RABBITMQ_DLQ: str = "notification_dlq"
    RABBITMQ_ROUTING_KEY: str = "payroll.#"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@payroll.com"
    SMTP_FROM_NAME: str = "Payroll System"

    # Security
    AUTH_TOKEN: str = "secure-token"

    # Retry
    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
