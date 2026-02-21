import asyncio
import random
from app.config.logging import get_logger

logger = get_logger(__name__)


class SMSService:
    """
    Simulated SMS provider service.
    In production, replace _call_provider with actual SMS gateway (Twilio, MSG91, etc.)
    """

    @staticmethod
    async def _call_provider(phone: str, message: str) -> dict:
        """Simulate SMS provider call with random latency."""
        await asyncio.sleep(random.uniform(0.1, 0.4))  # Simulate network latency
        logger.info(
            "sms_mock_sent",
            phone_masked=phone[-4:].rjust(len(phone), "*"),
            message_preview=message[:60],
        )
        return {
            "provider": "MockSMSProvider",
            "message_id": f"SMS-{random.randint(100000, 999999)}",
            "status": "delivered",
        }

    @classmethod
    async def send(cls, phone: str, message: str) -> dict:
        """Send SMS notification. Returns result dict."""
        if not phone:
            raise ValueError("Phone number is required for SMS")

        try:
            result = await cls._call_provider(phone, message)
            logger.info("sms_sent", message_id=result["message_id"])
            return {"status": "SENT", "message": f"SMS sent via {result['provider']}", "provider_result": result}
        except Exception as e:
            logger.error("sms_send_failed", phone_tail=phone[-4:], error=str(e))
            raise
