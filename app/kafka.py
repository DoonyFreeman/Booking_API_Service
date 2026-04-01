import json
import asyncio
import logging
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from app.config import settings

logger = logging.getLogger(__name__)

kafka_producer: AIOKafkaProducer | None = None

MAX_RETRIES = 10
RETRY_DELAY = 2


async def init_kafka() -> AIOKafkaProducer:
    global kafka_producer

    for attempt in range(MAX_RETRIES):
        try:
            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await kafka_producer.start()
            logger.info("Kafka connected successfully")
            return kafka_producer
        except KafkaConnectionError as e:
            logger.warning(
                f"Kafka not ready (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if kafka_producer:
                await kafka_producer.stop()
                kafka_producer = None
            await asyncio.sleep(RETRY_DELAY)

    raise KafkaConnectionError(
        f"Failed to connect to Kafka after {MAX_RETRIES} attempts"
    )


async def close_kafka() -> None:
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()


async def get_kafka() -> AIOKafkaProducer:
    if kafka_producer is None:
        return await init_kafka()
    return kafka_producer


async def send_booking_event(event_type: str, data: dict[str, Any]) -> None:
    producer = await get_kafka()
    event = {"type": event_type, **data}
    await producer.send_and_wait(
        settings.KAFKA_TOPIC_BOOKING_EVENTS,
        value=event,
    )
