import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.config.logging import setup_logging, get_logger
from app.db.base import init_db

setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    logger.info("service_starting", service=settings.APP_NAME)

    # Initialize DB tables (use Alembic for production migrations)
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.warning("database_init_skipped", reason=str(e))

    # Start RabbitMQ consumer in background
    consumer_task = None
    try:
        from app.consumers.payroll_consumer import consumer
        await consumer.connect()
        logger.info("rabbitmq_consumer_started")
    except Exception as e:
        logger.warning("rabbitmq_unavailable", reason=str(e))

    yield

    # Shutdown
    try:
        from app.consumers.payroll_consumer import consumer
        await consumer.close()
    except Exception:
        pass

    logger.info("service_stopped", service=settings.APP_NAME)


app = FastAPI(
    title="Notification Microservice",
    description=(
        "Event-driven notification service for the Payroll System. "
        "Consumes RabbitMQ events and delivers Email / SMS notifications."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
