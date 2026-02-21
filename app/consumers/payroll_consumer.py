import asyncio
import json
from typing import Optional

import aio_pika
from aio_pika import IncomingMessage, ExchangeType

from app.config import settings
from app.config.logging import get_logger
from app.db.base import AsyncSessionLocal
from app.services.notification_service import NotificationService
from app.services.retry_service import retry_with_backoff

logger = get_logger(__name__)


class PayrollEventConsumer:
    """
    Async RabbitMQ consumer that:
    - Connects to exchange with topic routing
    - Validates and processes each payroll event
    - Retries with exponential backoff on failure
    - Routes to DLQ after max retries
    """

    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._dlq_exchange: Optional[aio_pika.Exchange] = None

    async def connect(self) -> None:
        logger.info("rabbitmq_connecting", url=settings.RABBITMQ_URL[:30] + "...")
        self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Main exchange
        exchange = await self._channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True,
        )

        # Dead-letter exchange & queue
        dlq_exchange = await self._channel.declare_exchange(
            f"{settings.RABBITMQ_EXCHANGE}.dlx",
            ExchangeType.FANOUT,
            durable=True,
        )
        self._dlq_exchange = dlq_exchange

        dlq_queue = await self._channel.declare_queue(
            settings.RABBITMQ_DLQ,
            durable=True,
        )
        await dlq_queue.bind(dlq_exchange)

        # Main queue with DLQ routing
        queue = await self._channel.declare_queue(
            settings.RABBITMQ_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": f"{settings.RABBITMQ_EXCHANGE}.dlx",
            },
        )
        await queue.bind(exchange, routing_key=settings.RABBITMQ_ROUTING_KEY)

        await queue.consume(self._handle_message)
        logger.info("rabbitmq_consumer_started", queue=settings.RABBITMQ_QUEUE)

    async def _handle_message(self, message: IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                body = json.loads(message.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error("invalid_message_format", error=str(e))
                return  # discard malformed messages

            async def process(event_data: dict) -> None:
                async with AsyncSessionLocal() as db:
                    service = NotificationService(db)
                    await service.process_event(event_data)

            await retry_with_backoff(
                func=process,
                event_data=body,
                dlq_publisher=self._publish_to_dlq,
            )

    async def _publish_to_dlq(self, event_data: dict) -> None:
        if self._dlq_exchange:
            await self._dlq_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event_data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="",
            )
            logger.warning("message_sent_to_dlq", event_id=event_data.get("event_id"))

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            logger.info("rabbitmq_connection_closed")


consumer = PayrollEventConsumer()
