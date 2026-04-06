import asyncio
import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.services.notification_service import (
    send_booking_cancellation,
    send_booking_confirmation,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def process_event(event: dict[str, Any]) -> None:
    event_type = event.get("type")
    user_email = event.get("user_email", "")

    if not user_email:
        logger.warning(f"No user_email in event: {event}")
        return

    if event_type == "booking_created":
        await send_booking_confirmation(user_email, event)
    elif event_type == "booking_cancelled":
        await send_booking_cancellation(user_email, event)
    else:
        logger.warning(f"Unknown event type: {event_type}")


MAX_RETRIES = 10
RETRY_DELAY = 5


async def wait_for_kafka() -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_BOOKING_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="email-workers",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Connecting to Kafka (attempt {attempt}/{MAX_RETRIES})...")
            await consumer.start()
            logger.info("Kafka consumer started successfully")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka not ready: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                await consumer.stop()
                raise RuntimeError(
                    "Failed to connect to Kafka after maximum retries"
                ) from None

    raise RuntimeError("Should not reach here")


async def run_worker() -> None:
    logger.info("Starting email worker...")

    consumer = await wait_for_kafka()
    logger.info(f"Consumer started, listening to {settings.KAFKA_TOPIC_BOOKING_EVENTS}")

    try:
        async for msg in consumer:
            logger.info(f"Received message: {msg.value}")
            try:
                await process_event(msg.value)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    finally:
        await consumer.stop()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(run_worker())
