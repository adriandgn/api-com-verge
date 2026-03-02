from typing import Union

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from slowapi.errors import RateLimitExceeded

from api.database import get_registrations, insert_registration
from api.email_service import send_admin_notification, send_confirmation_email
from api.models import RegistrationPayload, RegistrationResponse
from api.rate_limit import limiter
from api.settings import get_settings


router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/registrations/{profile}", response_model=RegistrationResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def create_registration(
    profile: str,
    registration: RegistrationPayload,
    request: Request,
    background_tasks: BackgroundTasks
):
    valid_profiles = ["creator", "expert", "event-host", "participant", "volunteer"]
    if profile not in valid_profiles:
        raise HTTPException(status_code=400, detail=f"Invalid profile. Must be one of {valid_profiles}")

    if registration.profile != profile:
        raise HTTPException(status_code=400, detail="Profile in body does not match path")

    data = registration.model_dump(exclude={"profile"})
    email = data.get("email")
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    try:
        result = await insert_registration(
            profile=profile,
            data=data,
            email=email,
            ip=ip,
            user_agent=user_agent
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save registration")
    except Exception as exc:
        logger.exception("Error saving registration")
        raise HTTPException(status_code=500, detail=f"Error: {str(exc)}") from exc

    if email:
        name = data.get("name", "Usuario")
        try:
            background_tasks.add_task(send_confirmation_email, email, name, profile)
        except ValueError:
            logger.warning("Email config missing; confirmation email skipped")

    try:
        background_tasks.add_task(send_admin_notification, profile, data)
    except ValueError:
        logger.warning("Email config missing; admin notification skipped")

    return RegistrationResponse(
        success=True,
        message=f"{profile} registration created successfully",
        registration_id=result.get("uuid")
    )


@router.get("/registrations")
async def list_registrations(profile: str | None = None, limit: int = 100):
    try:
        registrations = await get_registrations(profile=profile, limit=limit)
        return {"success": True, "count": len(registrations), "data": registrations}
    except Exception as exc:
        logger.exception("Error listing registrations")
        raise HTTPException(status_code=500, detail=f"Error: {str(exc)}") from exc


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "registrations"}
