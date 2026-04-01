import logging
from email.message import EmailMessage
from typing import Any

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"SMTP not configured, skipping email to {to}")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


async def send_booking_confirmation(email: str, data: dict[str, Any]) -> bool:
    subject = f"Booking Confirmed #{data.get('booking_id')}"

    body = f"""
Hello!

Your booking has been confirmed!

Booking Details:
- Hall: {data.get("hall_name")}
- Date: {data.get("start_time", "").split("T")[0]}
- Time: {data.get("start_time", "").split("T")[1][:5]} - {data.get("end_time", "").split("T")[1][:5]}
- Total Price: ${data.get("total_price")}

Thank you for using our service!

Best regards,
Booking API Team
"""

    return await send_email(email, subject, body)


async def send_booking_cancellation(email: str, data: dict[str, Any]) -> bool:
    subject = f"Booking Cancelled #{data.get('booking_id')}"

    body = f"""
Hello!

Your booking has been cancelled.

Booking Details:
- Hall: {data.get("hall_name")}
- Booking ID: {data.get("booking_id")}

If you didn't request this cancellation, please contact support.

Best regards,
Booking API Team
"""

    return await send_email(email, subject, body)
