from pathlib import Path
import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from api.settings import get_settings

logger = logging.getLogger(__name__)


def get_email_config() -> ConnectionConfig:
    settings = get_settings()
    if not settings.mail_username or not settings.mail_password or not settings.mail_from:
        raise ValueError("Email settings are incomplete")
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_STARTTLS=settings.mail_starttls,
        MAIL_SSL_TLS=settings.mail_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates"
    )


async def send_confirmation_email(email: str, name: str, profile: str) -> None:
    conf = get_email_config()
    message = MessageSchema(
        subject=f"Welcome to COM/VERGE as {profile.replace('-', ' ').title()}",
        recipients=[email],
        template_body={"name": name, "profile": profile.replace("-", " ").title()},
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="confirmation.html")
    logger.info("Confirmation email sent to %s", email)


async def send_admin_notification(profile: str, data: dict) -> None:
    conf = get_email_config()
    settings = get_settings()
    message = MessageSchema(
        subject=f"New registration: {profile}",
        recipients=[settings.admin_email],
        template_body={"profile": profile, "data": data},
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="notification.html")
    logger.info("Admin notification sent to %s for profile %s", settings.admin_email, profile)


async def send_sponsor_confirmation_email(email: str, name: str) -> None:
    conf = get_email_config()
    message = MessageSchema(
        subject="Thanks for your interest in sponsoring COM/VERGENCE",
        recipients=[email],
        template_body={"name": name},
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="sponsor_confirmation.html")
    logger.info("Sponsor confirmation email sent to %s", email)


async def send_sponsor_admin_notification(data: dict) -> None:
    conf = get_email_config()
    settings = get_settings()
    message = MessageSchema(
        subject="New sponsor inquiry",
        recipients=[settings.admin_email],
        template_body={"data": data},
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="sponsor_notification.html")
    logger.info("Sponsor admin notification sent to %s", settings.admin_email)
