import json
from typing import Any

from aiokafka import AIOKafkaProducer

from app.config import settings

kafka_producer: AIOKafkaProducer | None = None


async def init_kafka() -> AIOKafkaProducer:
    global kafka_producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )
    await kafka_producer.start()
    return kafka_producer


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
